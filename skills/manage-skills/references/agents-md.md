# AGENTS.md wiring for skills

AGENTS.md is the project's always-loaded instruction file; skills load on demand. User-level
skills stay project-agnostic and read a project's conventions from AGENTS.md at run time.
Claude Code reads `CLAUDE.md`, so keep a `CLAUDE.md` that imports the shared file:

```markdown
@AGENTS.md
```

## Sections skills read and write

The `init-agent-conventions` skill writes and refreshes these sections; its
`references/conventions-schema.md` is the authoritative list of keys.

Keep keys short and stable so skills can find them. Add only what the repo actually uses.
Example (values are illustrative):

```markdown
## Agent workflow conventions
- Branch model: task branches → `feature/<epic>` → `staging` → `main`
- PR base: the epic's feature branch for task PRs; `staging` for feature PRs
- Protected: `staging`, `main` (`staging` → `main` needs explicit approval)
- Branch naming: `<type>/<issue-id>-<short-desc>`
- Merge method: rebase and merge
- Tracker: Beads (`bd`), IDs like `bd-123`
- Specs: `docs/tasks/<issue-id>.md`
- Checks before push: `pnpm nx affected -t lint,test,typecheck`

## Skills used in this repo
- `commit-push-pr`: commits, pushes and opens PRs using the conventions above
- `plan-feature` → `critique-plan` → `implement-feature`: feature delivery chain
- Project skills live in `.agents/skills/` (linked from `.claude/skills/`)
```

## Rules for skills
- Read conventions from these sections; never hardcode them.
- Missing value: detect a default, state the assumption, confirm with the user, then offer to
  add the line here, showing the diff first. Never edit AGENTS.md without approval.
- When creating a skill, offer to add it under "Skills used in this repo" (diff first).
