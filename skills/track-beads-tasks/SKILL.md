---
name: track-beads-tasks
description: "Manages task tracking with Beads (`bd`) or the Beads MCP: creating epics and tasks, linking specs, setting parents and dependencies, claiming and closing work, and syncing Dolt state. Use when the user mentions beads, bd, Dolt, epics, task specs, issue dependencies, child tasks, or session-close tracking."
---

# Track Beads tasks

## Preflight

Use this skill only when the repo uses Beads: `bd` is installed (`command -v bd`) and the repo has
a Beads database (`.beads/`), or the Beads MCP is connected. If not, say so and stop; do not
initialise Beads unless the user asks. Spec file locations come from AGENTS.md (`Specs:`, e.g.
`docs/tasks/<issue-id>.md`); `<spec-path>` below means that path.

Use Beads as the source of truth for task tracking. Do not replace it with markdown TODO lists.

## Quick Rules

- Run `bd prime` after context loss, compaction, or when the workflow is unclear.
- Prefer official Beads MCP tools for structured issue reads and mutations when available.
- Pass the exact repository root as `workspace_root`; call the MCP `context` tool before the first write.
- Use official Beads MCP or CLI directly within the user's authorized task scope and the current
  repository instructions. Reuse existing authorization for routine task updates and synchronization.
- If `context` misses an existing embedded-Dolt database, do not initialize it; verify with an explicit
  `workspace_root` read and continue passing that root to every operation.
- Use `bd ready`, `bd show <id>`, `bd update <id> --claim`, and `bd close <id>` when MCP is unavailable.
- Use the CLI for `bd prime`, `bd dolt push`/`pull`, diagnostics, linting, and unsupported operations.
- Use `bd remember "..."` for persistent workflow knowledge. Do not create `MEMORY.md`.
- Every task spec should live at `docs/tasks/<issue-id>.md`.
- Every task issue description should start with:

```text
Spec: docs/tasks/<issue-id>.md
```

## Creating Stable Child Tasks

Beads does not allow `--id` and `--parent` in the same `bd create` command.

Use this sequence for stable child task IDs:

```bash
bd create --id <child-id> --type task --priority P1 --title "<title>" \
  --description "Spec: <spec-path>

<summary>" \
  --acceptance "<testable acceptance criteria>"

bd update <child-id> --parent <epic-id> --spec-id <spec-path>
```

Then add ordering dependencies separately:

```bash
bd dep add <downstream-id> <upstream-id>
```

This means `<downstream-id>` depends on `<upstream-id>`.

## Creating Epics

Use stable epic IDs when the roadmap name is known:

```bash
bd create --id <epic-id> --type epic --priority P1 --title "<title>" \
  --description "Spec: docs/tasks/<epic-id>.md

<objective>" \
  --acceptance "<epic-level acceptance criteria>"
```

Create `docs/tasks/<epic-id>.md` with objective, capability map, proposed task chain, architecture diagram, and Definition of Done.

## Task Specs

Each child spec should include:

- Summary
- Requirements
- Implementation plan
- Dependency order
- Tests and verification
- Definition of Done

Keep Beads dependencies and the spec dependency table aligned. If they disagree, fix Beads first.

## MCP Boundary

The official Beads MCP exposes structured issue operations; it does not synchronize the Dolt remote
or provide durable orchestration checkpoints, pipeline waits, artifact storage, retry state, or
role-based authorization. Do not report task state as remotely synced until `bd dolt push` succeeds.
Respect the current repository's task ownership and the actual session permissions when updating
issues. A read-only review assignment does not authorize mutations merely because write tools exist.

## Branch Workflow

Follow the branch model in the repo's AGENTS.md (`## Agent workflow conventions`: branch model,
PR base, protected branches). Do not assume branch names. If the section is missing, offer to run
the `init-agent-conventions` skill first. If the user declines, detect the
default branch, state the assumption, confirm with the user, and offer to record the model in
AGENTS.md (show the diff first). Never commit implementation work directly to a protected branch.

## Sync And Closeout

At session close:

```bash
git status --short --branch
git add <files>
git commit -m "<message>"
git push
```

If any Beads command reports Dolt auto-push failure, tell the user to run:

```bash
bd dolt push
```

If the user says `bd dolt push` completed, treat Beads remote state as synced.
