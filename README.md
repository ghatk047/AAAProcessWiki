# AAA / CAA Process Wiki

A static, searchable business-process wiki for the AAA and CAA membership, insurance, roadside, travel, claims and financial-services organisations. The site describes itself as an "end-to-end process reference for AAA Northeast and CAA South Central Ontario - SAP consulting use cases". Each process has a description, attributes, a BPMN-style flow diagram and a step-by-step table that names the systems used (for example Guidewire, Salesforce, SAP S/4HANA).

Intended readers: SAP and business-process consultants, solution architects and analysts who want a structured reference model of AAA / CAA operations and the system landscape behind them.

> **Disclaimer.** This content is an independently compiled reference model. It is illustrative, was generated with AI assistance, and is not an official or validated description of any organisation's processes or systems. It is not affiliated with, endorsed by, or sponsored by AAA, CAA, CSAA, AAA Northeast, CAA South Central Ontario or any vendor named in the content. Company and product names are used only to describe a reference scenario.

## Live site

https://ghatk047.github.io/AAAProcessWiki/ (GitHub Pages, built from the `main` branch by GitHub Actions; the URL is also given in `CLAUDE.md`).

## What is in the wiki

Hierarchy: **L1 domain > L2 process group > L3 process > L4 steps**. L4 steps are rows in a table on each full process page.

| Item | Count |
|---|---|
| L1 domains (plus Enterprise Architecture) | 11 |
| Process pages | 268 (AAA 70, CAA 54, Shared 144) |
| Enterprise Architecture (EA) diagram pages | 8 |
| PNG diagrams in `assets/img/` | 239 |

Domains (folder, process-ID prefix and count, from `search-index.json`):

| Folder | L1 domain | L2 groups (ID prefix) | Processes |
|---|---|---|---|
| `shared-membership` | Membership Management | Enrolment `SHARED-MB-EN`, Renewal `SHARED-MB-RN`, Member Services `SHARED-MB-SV` | 24 |
| `aaa-insurance` | AAA Insurance | Quoting `AAA-IN-QU` (10), Policy Admin `AAA-IN-PO`, Billing `AAA-IN-BI`, Agency Ops `AAA-IN-AG` | 34 |
| `caa-insurance` | CAA Insurance (Ontario) | Quoting `CAA-CI-QU` (10), Policy Admin `CAA-CI-PO`, Billing `CAA-CI-BI`, Agency & Broker Ops `CAA-CI-AG` | 34 |
| `shared-roadside` | Roadside Assistance | Dispatch `SHARED-RS-DI`, Service Delivery `SHARED-RS-SV`, Provider Network `SHARED-RS-NW` | 24 |
| `shared-travel` | Travel Agency & Packages | Booking `SHARED-TR-BK`, Client Mgmt `SHARED-TR-CL`, Vacations `SHARED-TR-VK` | 24 |
| `aaa-financial` | AAA Financial Services | Banking `AAA-FS-BK`, Lending `AAA-FS-LN` | 16 |
| `shared-claims` | Claims Management | FNOL `SHARED-CL-FN`, Adjudication `SHARED-CL-AD`, Subrogation `SHARED-CL-SP` | 24 |
| `shared-automotive` | Automotive Services | Auto Repair `SHARED-AS-AR`, Driver Training `SHARED-AS-DT` | 16 |
| `shared-digital` | Digital & Technology | Digital Platforms `AAA-DT-DP` / `CAA-DT-DP`, IT Ops & Cybersecurity `AAA-DT-IT` / `CAA-DT-IT` (10 each) | 40 |
| `shared-hr` | Human Resources & Workforce | Workforce `SHARED-HR-WF`, Talent `SHARED-HR-TA` | 16 |
| `shared-marketing` | Marketing & Member Experience | Brand `SHARED-MK-BR`, Member Experience `SHARED-MK-CX` | 16 |
| `ea` | Enterprise Architecture | EA-01 to EA-08 | 8 pages |

Unlisted L2 groups have 8 processes. EA diagrams: EA-01 AAA Enterprise System Landscape, EA-02 CAA SCO Enterprise System Landscape, EA-03 Insurance Claims Data Flow, EA-04 Member Lifecycle Data Flow, EA-05 Travel Booking Architecture, EA-06 Roadside Assistance Dispatch Architecture, EA-07 CAA Insurance Policy Lifecycle, EA-08 CAA Insurance Claims Architecture.

### ID scheme and URL layout

Process ID: `{ORG}-{L1 code}-{L2 code}-{NN}`, where ORG is `AAA`, `CAA` or `SHARED`. Examples: `AAA-IN-QU-01`, `CAA-CI-PO-03`, `SHARED-MB-EN-01`. The file name is the lower-cased ID.

| Page type | Path | Asset prefix |
|---|---|---|
| Home | `index.html` | `assets/` |
| Process page | `<l1-folder>/<l2-folder>/<pid>.html` (two levels deep) | `../../assets/` |
| EA page | `ea/ea-NN.html` (one level deep) | `../assets/` |
| Diagram | `assets/img/<pid>.png`, `assets/img/ea-NN.png` | |

Example: `aaa-insurance/insurance-quoting/aaa-in-qu-01.html` uses `assets/img/aaa-in-qu-01.png`.

## Repository layout

```
.
├── index.html            Home page: overall and per-domain completion counts, EA entry
├── search.html           Search results page (fetches search-index.json)
├── search-index.json     Search data, 276 entries (268 processes + 8 EA): pid, l1, l2, l3, org, url, systems
├── assets/
│   ├── css/wiki.css      Shared styles, including system tag colours (AAA D3, Bringg, ACE, ...)
│   ├── js/wiki.js        Sidebar collapse, search, diagram lightbox / zoom and pan
│   └── img/              239 PNG diagrams
├── <11 L1 folders>/      shared-*, aaa-insurance, caa-insurance, aaa-financial
│   └── <L2 folder>/      process pages
├── ea/                   ea-01.html ... ea-08.html
├── scripts/
│   └── fix_bpmn_ordering.py   Sanitise / re-render / push tool for local Mermaid sources
├── .github/workflows/deploy.yml   GitHub Pages deployment (on push to main)
├── .deploy               Timestamp marker file; a final commit touching it triggers one clean Pages run
├── .nojekyll
├── .gitignore            Ignores processes.json, *.pyc, __pycache__/, .DS_Store
└── CLAUDE.md             Constraints for AI/agent-assisted authoring
```

No build step or package manager: the repo contains pre-generated static HTML, CSS, JS and PNG files.

## View locally

```bash
python3 -m http.server 8000      # from the repo root
# open http://localhost:8000/
```

Pages use relative paths and `search.html` fetches `search-index.json` relatively, so serving the repo root is enough.

## Regenerate / validate

The only tool in the repo is `scripts/fix_bpmn_ordering.py`. It operates on **local** Mermaid sources that are not committed: it expects a `diagrams/` folder of `<pid-lowercase>.mmd` files at the repo root (the folder does not exist in the repo). It:

- sanitises each `.mmd` (strips `|edge labels|`, markdown fences and YAML front matter, fixes HTML-encoded arrows, digit-leading node IDs, bare labels, missing `%%{init}%%` header, blank line after init, and adds inter-phase connector arrows so BPMN phases render in order),
- renders PNGs with the Mermaid CLI (`mmdc`, 1920x1080, scale 2, white background) into `assets/img/`,
- pushes changed files to GitHub in batches via the Git Data (tree) API and then updates `.deploy`.

Usage (from the script's docstring and `--help`):

```bash
python3 scripts/fix_bpmn_ordering.py --help
python3 scripts/fix_bpmn_ordering.py --audit            # scan only, no changes
python3 scripts/fix_bpmn_ordering.py --dry-run          # fix + render, no push
python3 scripts/fix_bpmn_ordering.py --only SHARED-AS-DT-06
python3 scripts/fix_bpmn_ordering.py --start SHARED-RS-DI-01
python3 scripts/fix_bpmn_ordering.py --force-rerender   # re-render all even if unchanged
python3 scripts/fix_bpmn_ordering.py                    # fix + render + push all
```

Prerequisites: Python 3 with `requests`, the `mmdc` CLI on `PATH`, and a local `diagrams/` folder. Warning: without `--audit` or `--dry-run` the script **pushes directly to `main`** via the GitHub API. It needs a GitHub token set in the `TOKEN` constant, which is a placeholder in the committed file; never commit a real token. The script only regenerates diagrams; it does not create or edit the process HTML pages. There is no automated test or link checker in the repo.

Deployment: `.github/workflows/deploy.yml` ("Deploy AAA-CAA Wiki to GitHub Pages") runs on every push to `main`, uploads the entire repo root (`path: '.'`) and deploys with `actions/deploy-pages`.

## Current status

Counted from the files in this repo:

- **Full process pages (description, BPMN diagram, L4 steps table): 229 of 268.** All 70 AAA and 144 Shared processes are full pages, but only 15 of the 54 CAA processes are (all 8 `CAA-CI-AG`, plus `CAA-CI-QU-09/10`, `CAA-CI-PO-06/08`, `CAA-CI-BI-07/08`, `CAA-DT-IT-07`).
- **"Mirror" stub pages: 39 CAA processes.** These contain only a short list of CAA-specific differences, a process attributes table and a link to the equivalent AAA page ("This CAA process mirrors AAA-... in structure"): `CAA-CI-QU-01` to `08` (8), `CAA-CI-PO` (6), `CAA-CI-BI` (6), `CAA-DT-DP-01` to `10` (10), `CAA-DT-IT-01` to `06` and `08` to `10` (9). They have no diagram or L4 table of their own.
- All 276 `search-index.json` entries resolve to existing pages. The home page states "268 Processes Complete", which counts these stubs as complete.
- PNG diagrams: 228 process diagrams used by full pages, 8 EA diagrams, and 3 extra PNGs (`caa-dt-it-04` to `06`) that belong to stub pages and are not displayed.
- Known gap: `SHARED-AS-DT-06` (Driver Training) references `assets/img/shared-as-dt-06.png`, which is not in the repo, so its diagram is broken.
- The recent history is mostly fixes: BPMN sanitiser passes over 231 diagrams, sidebar L3 links, adding the AAA D3 Dispatch system tags to the roadside pages and EA diagrams, and the search index `systems` field.

Remaining work:

1. Expand the 39 CAA stub pages into full pages with their own BPMN diagram and L4 steps (or keep them as deliberate mirrors and update the "complete" counters on the home page to say so).
2. Add the missing `shared-as-dt-06.png`.
3. Add a link/asset checker, since none exists.

## Continuing and contributing

Constraints from `CLAUDE.md`:

- Never commit a GitHub token. `processes.json` (the master process data) is local only and listed in `.gitignore`; never push it. The Excel catalogue mentioned in `CLAUDE.md` is also local; write to it only after a verified HTTP 200 and use plain ASCII statuses `Queued` / `Complete` (no emoji).
- Push many files with the Git Tree API in batches, not one Contents API PUT per file. The final commit of a batch updates `.deploy` so Pages runs once.
- Mermaid: `%%{init}%%` on line 1, no YAML front matter, no blank line before the `flowchart` line; node IDs start with a letter (`S1_1`, not `1.1`); arrows are `-->` only (never `--gt` or `--&gt;`).
- Process pages live at `l1_slug/l2_slug/pid.html` and load assets from `../../assets/`; EA pages live at `ea/ea-NN.html` and load from `../assets/`.
- PID format `{ORG}-{L1_CODE}-{L2_CODE}-{NN}`.

Gotchas:

- When you add or rename a page, update `search-index.json`, the sidebar (embedded in every page), and the counters on `index.html`.
- Commit messages used so far: `feat: ...`, `fix: ...`, `chore: ...`, and `deploy: <timestamp>` for the `.deploy` marker.
- The wiki is public; do not add credentials, tokens, customer data or any confidential material.

## Related repositories

Other wikis by the same owner (for example Hotel-Process-Wiki) follow the same static template (`assets/css/wiki.css`, `assets/js/wiki.js`, `search-index.json`, an EA section). Folder naming and ID formats differ per repo.
