#!/usr/bin/env python3
"""
fix_bpmn_ordering.py — Complete BPMN fix: ordering + all known sanitiser issues.

Fixes applied to every .mmd file:
  1. Inter-phase connector arrows  (prevents reversed P3/P2/P1 render order)
  2. Pipe | stripped from node labels  (breaks Mermaid link syntax)
  3. Bare source-node underscore labels: "NodeID Word_Word -->" -> "NodeID[Word_Word] -->"
  4. Bare arrow-target labels: "--> NodeID bare text" -> "--> NodeID[bare text]"
  5. HTML-encoded arrows, digit-start node IDs, markdown fences
  6. Blank line between %%{init} and flowchart

Usage:
  python3 scripts/fix_bpmn_ordering.py --audit       # scan only, no changes
  python3 scripts/fix_bpmn_ordering.py --dry-run     # fix + render, no push
  python3 scripts/fix_bpmn_ordering.py               # fix + render + push all
  python3 scripts/fix_bpmn_ordering.py --only SHARED-AS-DT-06
  python3 scripts/fix_bpmn_ordering.py --start SHARED-RS-DI-01
  python3 scripts/fix_bpmn_ordering.py --force-rerender  # re-render all even if unchanged
"""

import argparse, base64, re, subprocess, sys, time
from collections import defaultdict
from pathlib import Path
import requests

# ── Config ─────────────────────────────────────────────────────────────────────
OWNER     = "ghatk047"
REPO      = "AAAProcessWiki"
BRANCH    = "main"
TOKEN     = "ghp_YOUR_TOKEN_HERE"
BASE_DIR  = Path(__file__).resolve().parent.parent
DIAG_DIR  = BASE_DIR / "diagrams"
ASSET_DIR = BASE_DIR / "assets" / "img"

GH_HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept":        "application/vnd.github.v3+json",
    "Content-Type":  "application/json",
}

SKIP_KEYWORDS = {'end', 'subgraph', 'flowchart', 'graph', 'style',
                 'classdef', 'class', 'direction', 'click', 'linkstyle'}


# ── Comprehensive sanitiser ────────────────────────────────────────────────────
def comprehensive_sanitise(mmd: str) -> tuple:
    """
    Apply ALL known fixes to a mermaid diagram string.
    Returns (fixed_mmd, list_of_fix_labels).
    """
    fixes = []

    # 0. Strip -->|edge label| syntax — must run FIRST
    # Dangling -->|label| with no target breaks the parser entirely
    # Also strips valid -->|label| target -> --> target
    mmd = re.sub(r'\s*-->\s*\|[^|]*\|\s*$', '', mmd, flags=re.MULTILINE)
    mmd = re.sub(r'-->\s*\|[^|]*\|\s*', '--> ', mmd)

    # 1. Strip markdown fences
    mmd = re.sub(r'^```[a-z]*\n?', '', mmd, flags=re.MULTILINE)
    mmd = re.sub(r'```$',          '', mmd, flags=re.MULTILINE)

    # 2. Remove YAML frontmatter
    mmd = re.sub(r'^---.*?---\s*', '', mmd, flags=re.DOTALL)

    # 3. Fix HTML-encoded arrows
    if '--&gt;' in mmd or '--gt' in mmd:
        mmd = mmd.replace('--&gt;', '-->').replace('--gt', '-->')
        fixes.append("arrow-encoding")

    # 4. Fix digit-start node IDs: 1.1 -> S1_1
    if re.search(r'\b\d+\.\d+\b', mmd):
        mmd = re.sub(r'\b(\d+)\.(\d+)\b', r'S\1_\2', mmd)
        fixes.append("digit-nodes")

    # 5. Strip ()&<>| from inside node labels [...] and (...)
    def clean_label(m):
        text = re.sub(r'[()&<>|]', '', m.group(2))
        text = re.sub(r'\s{2,}', ' ', text).strip()
        return f'{m.group(1)}{text}{m.group(3)}'

    before = mmd
    mmd = re.sub(r'(\[)([^\]]+)(\])', clean_label, mmd)
    mmd = re.sub(r'(\()([^)]+)(\))', clean_label, mmd)
    if mmd != before:
        fixes.append("label-chars")

    # 6. Per-line fixes: bare labels (source and target)
    fixed_lines  = []
    line_fix_cnt = 0

    for line in mmd.split('\n'):
        s = line.strip()
        orig = line

        # Determine if this is a special/non-node line
        is_special = (not s or s[0] == '%' or
                      any(s.startswith(kw) for kw in
                          {'%%', 'subgraph', 'end', 'style', 'classDef',
                           'class ', 'flowchart', 'graph', 'direction',
                           'click', 'linkstyle'}))

        if not is_special:
            # Fix 6a: arrow-TARGET bare label: --> NodeID bare text
            # Only on lines without | (pipe confuses the regex)
            if '|' not in line:
                line = re.sub(
                    r'(--+>)\s*([A-Za-z]\w*)\s+([A-Za-z][^\[(\|\n][^\n]*)',
                    lambda m: (
                        f'{m.group(1)}{m.group(2)}'
                        f'[{re.sub(chr(40)+chr(41)+"&<>|","",m.group(2)+" "+m.group(3)).strip()}]'
                    ),
                    line)

            # Fix 6b: arrow-SOURCE bare UNDERSCORE label: NodeID Word_Word -->
            # e.g. "  Step1 SEO_Audit -->Step2" -> "  Step1[SEO_Audit] -->Step2"
            line = re.sub(
                r'\b([A-Za-z]\w*)\s+([A-Za-z]\w*_\w+)\s*(-->)',
                lambda m: f'{m.group(1)}[{m.group(2)}] {m.group(3)}',
                line)

            # Fix 6c: arrow-SOURCE bare MULTI-WORD label (lowercase words)
            # e.g. "  NodeA some action text -->NodeB"
            # Only trigger when there are NO brackets before the arrow
            def fix_multiword_source(m):
                before_arrow = m.group(0).split('-->')[0]
                if '[' in before_arrow:
                    return m.group(0)  # already has brackets
                nid   = m.group(1)
                label = m.group(2).strip()
                arrow = m.group(3)
                return f'{nid}[{label}]{arrow}'

            line = re.sub(
                r'\b([A-Za-z]\w*)\s+([a-z][a-z\s]{3,35}?)\s*(-->)',
                fix_multiword_source,
                line)

        if line != orig:
            line_fix_cnt += 1
        fixed_lines.append(line)

    if line_fix_cnt:
        fixes.append(f"bare-labels({line_fix_cnt})")
    mmd = '\n'.join(fixed_lines)

    # 7. Ensure %%{init} on line 1
    if '%%{init' not in mmd:
        mmd = "%%{init: {'theme':'base','themeVariables':{'fontSize':'13px'}}}%%\n" + mmd
        fixes.append("init-added")

    # 8. Remove blank lines between %%{init}%% and flowchart directive
    lines_out, cleaned = mmd.strip().split('\n'), []
    for ln in lines_out:
        if (cleaned and cleaned[-1].strip().startswith('%%{init')
                and ln.strip() == ''):
            continue
        cleaned.append(ln)
    mmd = '\n'.join(cleaned).strip()

    return mmd, fixes


def _ensure_phase_connectors(mmd: str) -> tuple:
    """
    Inject inter-phase connector arrows if missing.
    Returns (fixed_mmd, list_of_injected_connector_strings).
    Handles chained arrows: A1 --> A2 --> A3 on one line.
    """
    lines      = mmd.split('\n')
    subgraphs  = {}
    current_sg = None

    for line in lines:
        s = line.strip()
        sg = re.match(r'^subgraph\s+(P\d+)\s*[\[\{]', s)
        if sg:
            current_sg = sg.group(1)
            subgraphs[current_sg] = []
            continue
        if s == 'end':
            current_sg = None
            continue
        if current_sg is None:
            continue
        if s.startswith('style ') or s.startswith('classDef'):
            continue
        # Extract all node IDs from line (handles chains)
        nids = re.findall(r'\b([A-Za-z]\w*)(?:\s*[\[\(]|\s*-->)', line)
        for nid in nids:
            if nid.lower() not in SKIP_KEYWORDS and nid not in subgraphs[current_sg]:
                subgraphs[current_sg].append(nid)

    phases     = sorted(subgraphs.keys())
    injections = []

    for i in range(len(phases) - 1):
        nc = subgraphs.get(phases[i],     [])
        nn = subgraphs.get(phases[i + 1], [])
        if not nc or not nn:
            continue
        last_c, first_n = nc[-1], nn[0]
        if (f'{last_c} --> {first_n}' not in mmd and
                f'{last_c}-->{first_n}' not in mmd):
            injections.append(f'  {last_c} --> {first_n}')

    if injections:
        style_idx = next((i for i, l in enumerate(lines)
                          if l.strip().startswith('style ')), None)
        if style_idx is not None:
            lines = lines[:style_idx] + injections + lines[style_idx:]
        else:
            lines = lines + injections

    return '\n'.join(lines), [s.strip() for s in injections]


def full_fix(mmd: str) -> tuple:
    """Sanitise + phase connectors. Returns (fixed_mmd, all_fix_labels)."""
    mmd, san   = comprehensive_sanitise(mmd)
    mmd, conns = _ensure_phase_connectors(mmd)
    all_fixes  = san + ([f"connectors({', '.join(conns)})"] if conns else [])
    return mmd, all_fixes


# ── Audit mode ─────────────────────────────────────────────────────────────────
def audit_all(mmds: list) -> dict:
    """Report issues per file without modifying anything."""
    issues = defaultdict(list)

    for mmd_path in mmds:
        pid = mmd_path.stem.upper()
        with open(mmd_path) as f:
            content = f.read()
        lines = content.split('\n')

        if not lines[0].strip().startswith('%%{init'):
            issues[pid].append(f"MISSING_INIT")

        for i, ln in enumerate(lines[:-1]):
            if ln.strip().startswith('%%{init') and lines[i+1].strip() == '':
                issues[pid].append(f"BLANK_AFTER_INIT:L{i+1}")

        if '--&gt;' in content or '--gt' in content:
            issues[pid].append("HTML_ARROW")

        for m in re.finditer(r'\[[^\]]*\|[^\]]*\]', content):
            issues[pid].append(f"PIPE_IN_LABEL: {m.group(0)[:50]}")
            break

        for i, ln in enumerate(lines, 1):
            s = ln.strip()
            if (not s or any(s.startswith(k) for k in
                             {'%%', 'subgraph', 'end', 'style', 'classDef',
                              'class ', 'flowchart', 'graph'})):
                continue
            if re.search(r'\b[A-Za-z]\w*\s+[A-Za-z]\w*_\w+\s*-->', ln):
                issues[pid].append(f"BARE_UNDERSCORE:L{i}: {s[:70]}")
            if (re.search(r'\b[A-Za-z]\w*\s+[a-z][a-z\s]{3,35}\s*-->', ln)
                    and '[' not in ln.split('-->')[0]):
                issues[pid].append(f"BARE_MULTIWORD:L{i}: {s[:70]}")

        # Missing phase connectors
        sgs, cur = {}, None
        for ln in lines:
            s = ln.strip()
            m = re.match(r'^subgraph\s+(P\d+)\s*[\[\{]', s)
            if m:
                cur = m.group(1)
                sgs[cur] = []
            elif s == 'end':
                cur = None
            elif cur:
                for nid in re.findall(r'\b([A-Za-z]\w*)(?:\s*[\[\(]|\s*-->)', ln):
                    if nid.lower() not in SKIP_KEYWORDS and nid not in sgs[cur]:
                        sgs[cur].append(nid)

        for i, ph in enumerate(sorted(sgs.keys())[:-1]):
            pnext = sorted(sgs.keys())[i + 1]
            nc, nn = sgs.get(ph, []), sgs.get(pnext, [])
            if nc and nn:
                lc, fn = nc[-1], nn[0]
                if f'{lc} --> {fn}' not in content and f'{lc}-->{fn}' not in content:
                    issues[pid].append(f"MISSING_CONNECTOR:{lc}-->{fn}")

    return issues


# ── mmdc render ────────────────────────────────────────────────────────────────
def render_png(mmd_path: Path, png_path: Path) -> tuple:
    for attempt in range(1, 4):
        res = subprocess.run(
            ["mmdc", "-i", str(mmd_path), "-o", str(png_path),
             "-w", "1920", "-H", "1080", "--scale", "2",
             "--backgroundColor", "white"],
            capture_output=True, text=True)
        if res.returncode == 0 and png_path.exists():
            return True, ""
        err = res.stderr.strip()[:200]
        if attempt < 3:
            time.sleep(1)
    return False, err


# ── GitHub helpers ─────────────────────────────────────────────────────────────
def gh_push_batch(files_dict: dict, message: str) -> str:
    r = requests.get(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}",
        headers=GH_HEADERS)
    r.raise_for_status()
    head_sha   = r.json()["object"]["sha"]
    tree_items = []

    for gh_path, content in files_dict.items():
        if isinstance(content, str):
            content = content.encode("utf-8")
        if len(content) / 1_048_576 > 95:
            print(f"  SKIP {gh_path}: too large"); continue
        rb = requests.post(
            f"https://api.github.com/repos/{OWNER}/{REPO}/git/blobs",
            headers=GH_HEADERS,
            json={"content": base64.b64encode(content).decode(),
                  "encoding": "base64"})
        if not rb.ok:
            print(f"  BLOB ERROR {gh_path}: {rb.status_code} {rb.text[:200]}")
            rb.raise_for_status()
        tree_items.append({"path": gh_path, "mode": "100644",
                           "type": "blob", "sha": rb.json()["sha"]})

    rt = requests.post(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees",
        headers=GH_HEADERS,
        json={"base_tree": head_sha, "tree": tree_items})
    rt.raise_for_status()
    rc = requests.post(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/commits",
        headers=GH_HEADERS,
        json={"message": message, "tree": rt.json()["sha"],
              "parents": [head_sha]})
    rc.raise_for_status()
    ru = requests.patch(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}",
        headers=GH_HEADERS, json={"sha": rc.json()["sha"]})
    ru.raise_for_status()
    return rc.json()["sha"]


def gh_push_deploy_marker():
    from datetime import datetime
    ts  = datetime.now().isoformat()
    r   = requests.get(
        f"https://api.github.com/repos/{OWNER}/{REPO}/contents/.deploy",
        headers=GH_HEADERS)
    sha = r.json().get("sha") if r.ok else None
    payload = {"message": f"deploy: {ts}", "branch": BRANCH,
               "content": base64.b64encode(ts.encode()).decode()}
    if sha:
        payload["sha"] = sha
    requests.put(
        f"https://api.github.com/repos/{OWNER}/{REPO}/contents/.deploy",
        headers=GH_HEADERS, json=payload).raise_for_status()


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Fix BPMN phase ordering + all sanitiser issues")
    parser.add_argument("--audit",         action="store_true")
    parser.add_argument("--dry-run",       action="store_true")
    parser.add_argument("--only",          metavar="PID")
    parser.add_argument("--start",         metavar="PID")
    parser.add_argument("--batch-size",    type=int, default=50)
    parser.add_argument("--force-rerender",action="store_true",
                        help="Re-render ALL files even if .mmd unchanged")
    args = parser.parse_args()

    if not DIAG_DIR.exists() or not any(DIAG_DIR.glob("*.mmd")):
        print(f"ERROR: No .mmd files in {DIAG_DIR}")
        print("Run this script on your Mac Mini.")
        sys.exit(1)

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    all_mmds = sorted(DIAG_DIR.glob("*.mmd"))

    # ── Audit only ────────────────────────────────────────────────────────────
    if args.audit:
        print(f"AUDIT — {len(all_mmds)} .mmd files\n")
        issues    = audit_all(all_mmds)
        total_iss = sum(len(v) for v in issues.values())

        by_type = defaultdict(list)
        for pid, piss in issues.items():
            for iss in piss:
                by_type[iss.split(':')[0]].append(pid)

        print(f"{'='*70}")
        print(f"{len(issues)} PIDs with issues | {total_iss} total\n")
        print("SUMMARY BY TYPE:")
        for t, pids in sorted(by_type.items(), key=lambda x: -len(x[1])):
            print(f"  {t:<35} {len(pids):>4} PIDs")
        print("\nDETAIL:")
        for pid in sorted(issues.keys()):
            print(f"\n  [{pid}]")
            for iss in issues[pid]:
                print(f"    {iss}")
        return

    # ── Select targets ────────────────────────────────────────────────────────
    if args.only:
        target = [m for m in all_mmds if m.stem == args.only.lower()]
        if not target:
            print(f"ERROR: {args.only}.mmd not found"); sys.exit(1)
    elif args.start:
        sl  = args.start.lower()
        idx = next((i for i, m in enumerate(all_mmds) if m.stem >= sl), None)
        if idx is None:
            print(f"ERROR: no file >= {args.start}"); sys.exit(1)
        target = all_mmds[idx:]
    else:
        target = all_mmds

    print(f"Processing {len(target)} files "
          f"({'DRY RUN' if args.dry_run else 'LIVE'})\n")

    png_to_push    = {}
    render_failed  = []
    fixed_count    = 0
    clean_count    = 0

    for i, mmd_path in enumerate(target, 1):
        pid      = mmd_path.stem.upper()
        png_path = ASSET_DIR / f"{mmd_path.stem}.png"

        print(f"[{i:>3}/{len(target)}] {pid}", end=" ... ", flush=True)

        with open(mmd_path) as f:
            original = f.read()

        fixed, applied = full_fix(original)
        changed = fixed != original

        if changed:
            with open(mmd_path, 'w') as f:
                f.write(fixed)
            label = f"FIXED ({', '.join(applied)})"
            fixed_count += 1
        else:
            label = "clean"
            clean_count += 1

        should_render = changed or args.force_rerender or not png_path.exists()

        if not should_render:
            print(f"{label} | skip render (PNG exists)")
            continue

        print(f"{label}", end=" | ", flush=True)
        ok, err = render_png(mmd_path, png_path)

        if ok:
            sz = png_path.stat().st_size / 1024
            print(f"rendered ({sz:.0f}KB)")
            if not args.dry_run:
                png_to_push[f"assets/img/{mmd_path.stem}.png"] = \
                    png_path.read_bytes()
        else:
            print(f"RENDER FAILED: {err[:120]}")
            render_failed.append(pid)

    # ── Push ──────────────────────────────────────────────────────────────────
    if not args.dry_run and png_to_push:
        total  = len(png_to_push)
        keys   = list(png_to_push.keys())
        bs     = args.batch_size
        print(f"\nPushing {total} PNGs (batch {bs})...")
        for start in range(0, total, bs):
            bkeys = keys[start:start + bs]
            batch = {k: png_to_push[k] for k in bkeys}
            end   = min(start + bs, total)
            print(f"  {start+1}–{end}/{total}...", end=" ", flush=True)
            sha = gh_push_batch(
                batch,
                f"fix: BPMN sanitiser all issues ({start+1}-{end}/{total})")
            print(f"commit {sha[:12]}")

        print("  .deploy marker...", end=" ", flush=True)
        gh_push_deploy_marker()
        print("done")

    print(f"\n{'='*60}")
    print(f"  Fixed:         {fixed_count}")
    print(f"  Already clean: {clean_count}")
    print(f"  Render failed: {len(render_failed)}")
    if render_failed:
        print(f"\n  Failed PIDs:")
        for pid in render_failed:
            print(f"    {pid}")
        print(f"\n  Inspect with:")
        for pid in render_failed:
            print(f"    head -15 {DIAG_DIR}/{pid.lower()}.mmd")
        print(f"\n  Retry:")
        for pid in render_failed:
            print(f"    python3 scripts/fix_bpmn_ordering.py --only {pid}")
    if not args.dry_run and png_to_push:
        print(f"\n  Pushed: {len(png_to_push)} PNGs")
        print(f"  https://{OWNER}.github.io/{REPO}/")
        print(f"  ~90s for Pages propagation")
    elif args.dry_run:
        print(f"\n  [DRY RUN] nothing pushed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
