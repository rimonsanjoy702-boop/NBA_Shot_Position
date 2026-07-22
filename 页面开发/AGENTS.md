# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, etc.) when working in this repository.

> **Sync rule:** When any change is made to this file, the agent MUST apply the same change to `CLAUDE.md`, `.cursorrules`, and `.github/copilot-instructions.md` so all agent instruction files stay in sync. Edit `AGENTS.md` → update the other three. Edit `CLAUDE.md` → update the other three. The four files must always have identical content (only the title line differs — "CLAUDE.md" vs "AGENTS.md" etc.).

## Project Overview

A collaborative visual analytics project for an NBA shot locations dataset (1997–2020, ~4.7M records). Team of 3 members. The project involves data preprocessing (Python), a Vue 3 frontend with interactive visualizations, and a final presentation (July 24, 2026).

## Git Collaboration Rules

### Branch Strategy

- **Never commit directly to `main`.** Always work on a feature/personal branch.
- Branch naming: use a consistent prefix — `feat/`, `fix/`, `chore/`, `docs/` followed by a short kebab-case description.
- Create branches from an up-to-date `main`. Before starting any new work, run:
  ```
  git checkout main
  git pull origin main
  git checkout -b <branch-name>
  ```

### Commit Conventions

- Follow **Conventional Commits**: `<type>: <short description>`
- Allowed types: `feat`, `fix`, `chore`, `docs`, `refactor`, `style`, `test`
- One commit = one logical change. Do not bundle unrelated changes in one commit.
- Every commit must leave the project in a working state — no broken builds.
- Commit messages may be written in Chinese (team convention), but the type prefix stays in English.
- Write clear descriptions: the message alone should let a teammate understand what changed and why.

### Commit & Push Policy

- **Auto-commit:** Agent should commit frequently — every logical unit of work. Commit messages follow the Conventional Commits format above.
- **No auto-push:** Agent must NEVER push on its own. Pushing is a human decision.
- **Push workflow:**
  1. Agent completes a complete module (a feature, a fix, a data-processing step, etc.).
  2. Agent reminds the user: the module is done, commits are ready, here is a summary of what changed.
  3. Agent explicitly asks: **"是否推送?"** (Push now?)
  4. Only when the user confirms, Agent runs `git push`.
- **Before starting work each session:** `git pull origin main` to sync with teammates.
- **Before pushing,** always run the pre-push checklist below.

### Merging / Pull Requests

- When your feature is complete, push the branch and open a Pull Request on GitHub targeting `main`.
- At least one teammate must review and approve before merging.
- Resolve merge conflicts in your branch (not directly on main). When conflicts arise:
  1. `git checkout main && git pull origin main`
  2. `git checkout <your-branch> && git merge main` (or rebase)
  3. Resolve conflicts manually, test that everything works, then commit and push.

### What NOT to Commit

The `.gitignore` already covers these, but verify every commit:

- ❌ `node_modules/` — restored via `pnpm install`
- ❌ `*.csv` / `*.tsv` / `*.parquet` — raw data files
- ❌ `__pycache__/`, `*.pyc` — Python bytecode
- ❌ `venv/`, `.venv/` — Python virtual environments
- ❌ `.vscode/`, `.idea/` — personal IDE settings
- ❌ `dist/`, `.vite/` — build artifacts
- ❌ `*.zip`, `*.tar.gz`, `*.7z` — compressed archives
- ❌ `.DS_Store`, `Thumbs.db`, `desktop.ini` — OS junk

### Pre-Push Checklist

Before `git push`, always:
1. Run `git status` and verify only intended files are staged.
2. Confirm no ignored files leaked through (no `node_modules`, no `.csv`, no `__pycache__`).
3. If working on the frontend: verify `pnpm dev` starts without errors.
4. If working on Python: verify scripts produce expected output.

## Technology Stack

- **Frontend:** Vue 3 + Vite + pnpm + ECharts (vue-echarts) + D3.js + Element Plus
- **Data processing:** Python (pandas, numpy)
- **Node.js:** v22.17.0 LTS (required)
- **Package manager:** pnpm (do not use npm or yarn)
- **State management:** Pinia
- **Version control:** Git + GitHub

## Project Conventions

### File Organization

- Processed data for the frontend goes in `public/data/` as JSON files — not raw CSV.
- Python preprocessing scripts go in a `scripts/` or `processing/` directory at the project root.
- Vue components follow the standard Vite + Vue 3 project structure.

### Code Style

- Use the team's agreed shared design tokens (colors, spacing, fonts) as CSS variables — never hardcode visual values in components.
- Every view component must handle three states: normal, empty-data, and loading.
- Data flow: user action → Pinia store → all subscribed views respond. One-way, no exceptions.

### Before Claiming a Task Is "Done"

- The feature works end-to-end (data → store → view renders correctly).
- Cross-view linking still functions (if applicable).
- The three states (normal / empty / loading) all render correctly.
- No console errors or warnings remain.
- Code has been pushed and a PR is open or ready.

### Task Completion Report

When the agent finishes a task, it MUST report a summary including:

1. **What was done** — brief description of the completed work.
2. **Files changed** — list every file that was created, modified, or deleted, with its full path relative to the project root. Format: `- [x] path/to/file` (where x is `+` for new, `~` for modified, `-` for deleted).
3. **Next steps** (if any) — what remains to be done or what the user should do next.
