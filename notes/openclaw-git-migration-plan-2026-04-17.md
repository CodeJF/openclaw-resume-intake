# OpenClaw Git Migration Plan (2026-04-17)

## Goal
Use Alibaba Cloud OpenClaw business workspaces as the canonical starting point, publish them to GitHub, then have local macOS pull and continue future development locally. Server will later only git pull.

## Repos
- git@github.com:CodeJF/openclaw-main-workspace.git
- git@github.com:CodeJF/openclaw-interviewer.git
- git@github.com:CodeJF/openclaw-resume-intake.git

## Canonical sources
- main workspace: `/root/.openclaw/workspace`
- interviewer workspace: `/root/.openclaw/workspace-interviewer`
- resume-intake workspace: `/root/.openclaw/workspace-resume-intake`

## Must NOT be committed
- `.git/`
- `.DS_Store`
- runtime directories / caches / logs / tmp outputs
- secrets / auth / OAuth / credentials
- `.venv/`
- `__pycache__/`
- local config files like `config.local.json`
- server-only runtime data

## Special handling
- interviewer repo excludes `runtime/` and archive tarballs
- resume-intake repo excludes `.venv/`, `tmp/`, `__pycache__/`
- main repo excludes qr and migration tarballs by default

## Migration workflow
1. Backup server workspaces
2. Normalize `.gitignore`
3. Add GitHub remote to each canonical server repo
4. Commit sanitized server content
5. Push to GitHub
6. Point local repos to GitHub remotes
7. Pull/reconcile local copies
8. Future workflow: local commit/push, server pull
