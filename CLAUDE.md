# AAA / CAA Process Wiki — Agent Constraints

## Identity
This repo hosts the AAA / CAA Business Process Wiki for SAP consulting.
Primary reference: AAA Northeast + CSAA/ACG (AAA); CAA South Central Ontario (CAA).

## Hard Constraints
- GitHub token: stored locally only — never commit to repo
- processes.json: LOCAL ONLY — in .gitignore, never push
- All file pushes: Tree API batch (not individual Contents API PUT per file)
- Final commit per batch: .deploy marker triggers one clean GitHub Pages run
- Mermaid: %%{init}%% on line 1, no YAML frontmatter, no blank line before flowchart
- Node IDs must start with letter (S1_1 not 1.1)
- Arrows: --> only, never --gt or --&gt;
- Process pages: l1_slug/l2_slug/pid.html (2 levels deep → ../../assets/)
- EA pages: ea/ea-NN.html (1 level deep → ../assets/)
- Excel: write only after HTTP 200 verify; existence guard on startup
- Status in Excel: plain ASCII 'Queued'/'Complete' (no emoji)

## PID Format
{ORG}-{L1_CODE}-{L2_CODE}-{NN}
Examples: AAA-IN-QU-01, CAA-CI-PO-03, SHARED-MB-EN-01

## Repo
https://github.com/ghatk047/AAAProcessWiki
Live: https://ghatk047.github.io/AAAProcessWiki/
