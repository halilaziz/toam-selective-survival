# TOAM workspace (THOUGHTS project)

Secondary analysis of TOAM (Willems et al., bioRxiv 10.1101/2025.06.02.656652; OpenNeuro ds006265 + ds006266, CC0, tag 1.0.2).

**Golden rule (Halil 2026-11-12):** write, change or delete only inside `/analysis/halilaziz/halil/TOAM`; nothing outside it. Every script sources `code/env.sh`, which redirects HOME, TMPDIR and all caches into this folder.

## Layout
- `code/`: scripts (canonical copy on the Mac in `~/Downloads/THOUGHTS/toam/code`).
- `raw/ds006265`, `raw/ds006266`: git clones at tag 1.0.2. Imaging content sits in each clone's `.git/annex/objects`, so the BIDS symlinks resolve.
- `manifests/`: download manifest (path, size, SHA-256, URL), aria2 input and session files, verification report.
- `logs/`, `tmp/`: run logs and redirected caches and temp files.

## Steps
1. Run `bash code/setup.sh` to clone and build the manifest.
2. Run `bash code/start_download.sh` to start a detached, resumable download with SHA-256 checks.
3. Run `bash code/status.sh` to see progress.
4. Run `source code/env.sh && python3 code/verify.py` for the final audit.
