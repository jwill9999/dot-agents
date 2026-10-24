# Commit message rules (Conventional Commits 1.0.0)

Spec: https://www.conventionalcommits.org/en/v1.0.0/

## Format

```
<type>(<scope>): <subject>

<body>

<footer(s)>
```

## Types

| Type       | Use for                                                    |
|------------|------------------------------------------------------------|
| `feat`     | New user-facing capability                                 |
| `fix`      | Bug fix                                                    |
| `refactor` | Code change with no behaviour change                       |
| `perf`     | Performance improvement                                    |
| `test`     | Adding or fixing tests only                                |
| `docs`     | Documentation only                                         |
| `build`    | Build system, dependencies, package config                 |
| `ci`       | CI configuration and scripts                               |
| `chore`    | Maintenance that fits nothing above (avoid as a catch-all) |
| `style`    | Formatting only, no code meaning change                    |
| `revert`   | Reverting a previous commit                                |

## Scope (path-based, tool-agnostic)

- Derive from the paths changed: the most specific meaningful directory or package name,
  e.g. `auth`, `api`, `ui`, `config`, `deps`.
- In a monorepo, prefer the package/app folder name (`apps/<name>`, `libs/<name>`,
  `packages/<name>` → `<name>`).
- If a commit genuinely spans many areas, omit the scope rather than inventing a vague one.
  (Spanning many areas is also a hint the commit should be split.)

## Subject

- Imperative mood: "add", "fix", "extract" (not "added", "adds").
- Lower case, no trailing full stop, aim for ≤ 50 characters, hard limit 72.
- Says *what* changed in this commit, not the whole feature.

## Body

- Explain *why* the change was made and any important context or trade-offs.
- Wrap at 72 characters.
- Omit for trivial commits (e.g. typo fixes).

## Footers

- `Refs: <issue-id>` when the repo uses a tracker and an issue is known (format from
  AGENTS.md, e.g. `Refs: bd-123`).
- `BREAKING CHANGE: <description>` for breaking changes (and add `!` after the type/scope:
  `feat(api)!: drop v1 endpoints`).
- `Co-authored-by:` only if the user asks.

## Atomicity checklist (apply to each planned commit)

- [ ] One logical change; the subject describes it without "and".
- [ ] Can be reverted alone without breaking unrelated work.
- [ ] Can be cherry-picked onto another branch with only its stated dependencies.
- [ ] Leaves the build/tests green where practical.
- [ ] No unrelated formatting churn mixed in (put formatting in its own `style` commit).

## Examples

```
refactor(auth): extract token parser into its own module

Parsing logic was duplicated in session and middleware. Moving it
out first keeps the refresh-flow commit focused.

Refs: bd-42
```

```
feat(auth): add refresh-token flow

Access tokens now refresh silently when within 60s of expiry,
so long-running agent sessions no longer fail mid-task.

Refs: bd-42
```

```
fix(api)!: return 404 instead of 200 for missing sessions

BREAKING CHANGE: clients checking for an empty body must now
handle a 404 status.
```
