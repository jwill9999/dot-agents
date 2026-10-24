---
name: init-agent-conventions
description: Detects a repository's agent workflow facts (branch model, protected branches, merge method, tracker, checks, instruction files, project skills) and writes or refreshes the "Agent workflow conventions" section in AGENTS.md, a CLAUDE.md that imports it, and links for project skills. Use when the user asks to set up, initialise, refresh, check or fix agent conventions or AGENTS.md for a repo, when a repo has no conventions section, or when another skill reports that declared conventions don't match the repo.
---

# Initialise or refresh agent conventions

Gives a repository the committed, machine-readable conventions that user-level skills read
(`commit-push-pr`, `track-beads-tasks`, `verify-e2e-quality`, the planning skills), and keeps
them accurate over time. Writes nothing without showing a diff and getting approval.

## Modes

| Mode | When | Result |
|---|---|---|
| **Init** | AGENTS.md has no `## Agent workflow conventions` section | Full draft of the sections and wiring |
| **Refresh** | The section exists | Drift report: declared vs detected; proposed edits only where they differ |

Pick the mode from the detection report. Refresh never rewrites lines the user didn't approve.

## Scope (what this skill touches)

- In AGENTS.md: only `## Agent workflow conventions` and `## Skills used in this repo`.
  Everything else in AGENTS.md is left alone.
- If AGENTS.md doesn't exist (e.g. a new repo), create it with a `# Agent Instructions` title and
  just these two sections; the user can add commands, architecture and other guidance later.
- In a new or near-empty repo, detection finds little: ask for the intended branch model, tracker
  and checks rather than guessing, and mark undecided keys so later runs can fill them in.
- CLAUDE.md: imports AGENTS.md (`@AGENTS.md`) and keeps only Claude Code-specific notes.
- `.claude/skills/<name>` relative links for each project skill in `.agents/skills/`.
- Other tools' instruction files: reported, plus optional pointers (see step 6).

## Steps

1. **Detect** (read-only): `bash ~/.agents/skills/init-agent-conventions/scripts/detect.sh <repo>`.
   Then read AGENTS.md, CLAUDE.md and any instruction docs AGENTS.md links to (e.g. a shared
   instructions file); existing written rules outrank detection heuristics.

2. **Derive values** for each key in `references/conventions-schema.md`. Sources, in order:
   written rules in the repo's docs → GitHub settings via `gh` → local git/hooks/scripts →
   ask the user. Record where each value came from.

3. **Flag conflicts** between repo rules and skill defaults, e.g. a "must always push" rule
   vs confirm-before-push, a GitHub default branch that isn't the integration branch, or an
   autonomous-run broker that must own Git/tracker writes. Ask the user to resolve each one.

4. **Ask only about gaps** (unknown or ambiguous values), in one round.

5. **Draft** (init) or **diff** (refresh):
   - The two AGENTS.md sections using the schema's exact key names, with a maintenance comment
     and `Last verified: <YYYY-MM-DD>`.
   - CLAUDE.md: `@AGENTS.md` plus Claude Code-only notes. Move anything that applies to all
     agents (tracker rules, memory rules, setup commands) into AGENTS.md if it isn't already
     there; don't duplicate it. If CLAUDE.md has a tool-managed block (e.g. Beads markers),
     tell the user the tool may re-insert it.
   - Missing `.claude/skills` links: `ln -s ../../.agents/skills/<name> .claude/skills/<name>`.
   - Only include tracker lines if the repo uses that tracker.

6. **Other tools' instruction files** (e.g. `.github/copilot-instructions.md`, `GEMINI.md`,
   `.cursor/rules`): list them. Offer a one-line pointer to AGENTS.md only after checking that
   tool's current documentation confirms it reads that file or supports such a reference.
   Never delete or rewrite their content.

7. **Show everything as diffs** and get approval. Then write the files.

8. **Commit via `commit-push-pr`** so the change follows the repo's own branch model. On a
   repo whose model isn't declared yet, the newly drafted section is what it will use.

## Refresh report format

```
Declared vs detected:
  ✓ Protected: staging, main
  ✗ Checks before push: declared `pnpm test`; pre-push hook now also runs typecheck
  ? Merge method: declared rebase; GitHub allows squash too (warn only)
  + New project skill not listed: release-harness
Proposed edits: <diff>
```

## Rules

- Never commit or push directly; hand off to `commit-push-pr`.
- Never print secrets (`.env`, tokens); detection reads file names and key names only.
- Keep key names stable. Changing a key name is a schema change: update
  `references/conventions-schema.md` and every skill that reads the key in the same change.
