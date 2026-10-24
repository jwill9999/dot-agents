# Agent workflow conventions: key schema (v1)

The contract between `init-agent-conventions` (writer) and user-level skills (readers).
One line per key under `## Agent workflow conventions` in AGENTS.md: `- <Key>: <value>`.
Omit keys that don't apply. Readers treat a missing key as "detect, then confirm".

| Key | Meaning | Example | Read by |
|---|---|---|---|
| Branch model | How work flows between branches | `task/<name>` (chained) → `feature/<name>` → `staging` → `main` | commit-push-pr, track-beads-tasks, verify-e2e-quality |
| PR base | Which branch PRs target, per kind of branch | task tip → `feature/<name>`; feature → `staging` | commit-push-pr |
| Protected | Branches agents never commit or push to directly | `staging`, `main` | commit-push-pr, track-beads-tasks |
| Branch naming | Patterns for new branches | `feature/<name>`, `task/<name>` | commit-push-pr |
| Merge method | How PRs are merged | rebase and merge | commit-push-pr |
| Tracker | Issue tracker and ID format | Beads (`bd`), IDs like `proj-0k7` | commit-push-pr, track-beads-tasks |
| Specs | Where task specs live | `docs/tasks/<issue-id>.md` | track-beads-tasks, plan-feature |
| Checks before push | Commands or hooks that gate a push | `.husky/pre-push`; plus `pnpm lint` | commit-push-pr |
| Push policy | Whether pushes need confirmation | confirm / push without asking | commit-push-pr |
| Autonomous runs | Who owns Git/tracker writes during automated runs | journaled broker; no direct `git push` | commit-push-pr, track-beads-tasks |
| Last verified | Date the section was last checked against the repo | 2026-10-24 | all (staleness hint) |

Section header comment (keep it, so readers know where values come from):

```markdown
## Agent workflow conventions
<!-- Maintained by the init-agent-conventions skill; re-run it to refresh.
     Read by user-level skills. Keep key names stable. -->
```

Companion section:

```markdown
## Skills used in this repo
- Project skills (`.agents/skills/`, linked from `.claude/skills/`): <names>
- User-level skills: <names>
```
