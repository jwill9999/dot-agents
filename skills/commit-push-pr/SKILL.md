---
name: commit-push-pr
description: Commits, pushes and opens pull requests using small atomic Conventional Commits, following the repo's declared branch model, merge method and tracker. Use when the user asks to commit, checkpoint work, split changes into commits, tidy commits, push a branch, or create or open a PR.
---

# Commit, push and open PRs

Three phases that can run alone or in sequence: **Commit**, **Push**, **Pull request**.
Stop after the phase the user asked for ("just commit" means Phase 1 only).

Every phase ends with a confirmation step. Never run a commit, push, rewrite or PR command
without explicit user approval of what will happen. Exception: if the repo's conventions set
"Push policy: push without asking", ordinary pushes of the current non-protected branch go ahead
without asking (rewrites, `--force-with-lease`, commits and PRs still need approval).

This skill is project-agnostic. Branch names, protected branches, PR targets, merge method,
tracker and checks come from the repo's conventions (Phase 0), never from assumptions.

## Hard rules (never break these)

1. **No `--force`.** `--force-with-lease` only on the user's own non-protected branch, only
   after a history tidy or rebase, and only after confirmation.
2. **No `--no-verify`.** Hooks always run. If a hook fails, show the output and help fix the
   cause; never bypass it.
3. **No blind staging.** Never `git add -A`, `git add .` or `git commit -a`. Stage named files
   (or explicit patches) per planned commit.
4. **Protected branches** (from conventions): never commit to, rewrite or push to them directly.
5. **One logical change per commit.** Never fold unrelated changes together to save steps.

## Phase 0: Preflight and conventions (run before any phase)

```bash
git rev-parse --is-inside-work-tree
git branch --show-current
git status --short
git fetch origin --quiet
```
If a merge or rebase is in progress, stop and tell the user.

If the conventions say Git changes must go through a workflow broker while an autonomous run is
active, and such a run is active, do not run `git commit`, `git push` or `gh pr create` directly:
prepare the plan and messages, and hand them to that broker as the conventions describe.

### Read the repo's conventions
Read `AGENTS.md` at the repo root (and `CLAUDE.md` if present; it usually imports
`@AGENTS.md`). Look for a section like `## Agent workflow conventions` and extract:

| Key | Example | Used for |
|---|---|---|
| Branch model | task → `feature/<epic>` → `staging` → `main` | Which branch a PR targets |
| PR base | epic feature branch for task PRs; `staging` for feature PRs | `--base` |
| Protected | `staging`, `main` | Hard rule 4, branch creation |
| Merge method | rebase and merge | PR body note, merge-method check |
| Tracker | Beads (`bd`), IDs like `bd-123` | Commit footer, PR link, branch names |
| Branch naming | `<type>/<issue-id>-<desc>` | New branch names |
| Checks before push | `pnpm lint && pnpm format:check` | Phase 2 |
| Push policy | confirm (default) or push without asking | Phase 2 step 3 |
| Autonomous runs | Git changes go through a workflow broker | Whole skill |

The examples are illustrations only; use what the repo declares.

### Fill gaps: detect, then confirm
If the section is **missing entirely**, first offer to run the `init-agent-conventions` skill
(sets up the whole section in one pass). If **Last verified** is older than about 90 days, or a
declared value contradicts the repo (e.g. the PR base doesn't exist on the remote), mention that
`init-agent-conventions` can refresh it. Otherwise, or if the user declines:
For any key AGENTS.md doesn't declare, detect a default, **state the assumption, and ask the
user to confirm before acting**:
- Default branch: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
  (fallback: `git symbolic-ref --short refs/remotes/origin/HEAD`).
- Protected branches: the default branch, plus any from
  `gh api "repos/{owner}/{repo}/branches?protected=true" -q '.[].name'` (may need admin rights;
  if it fails, use the default branch and say so).
- Merge method: `gh repo view --json rebaseMergeAllowed,squashMergeAllowed,mergeCommitAllowed`.
- Tracker: Beads only if `bd` is installed and the repo has a Beads database (`.beads/`);
  otherwise no tracker unless the user names one.
- Checks: see Phase 2 step 1.

After confirming, **offer to record the missing values** in AGENTS.md under
`## Agent workflow conventions`, showing the exact diff first, so the next run doesn't ask again.
Never edit AGENTS.md without approval.

### Branch setup
- If on a protected branch: stop. Propose a branch from the branch-naming convention
  (default `<type>/<short-kebab-desc>`, or `<type>/<issue-id>-<short-kebab-desc>` when an issue
  ID is known) and create it on approval with `git switch -c <branch>` (uncommitted changes
  carry over). Cut it from the correct parent per the branch model (e.g. an epic's feature
  branch for a task).
- Issue ID (only if a tracker is in use): from the branch name, or ask once
  ("Is there a <tracker> issue for this? ID or 'none'"). Remember it for the session.

Throughout this skill, `<base>` means the PR base resolved here.

## Phase 1: Commit (atomic)

Read `references/commit-rules.md` before drafting messages.

1. **Inventory the changes**
   ```bash
   git status --short
   git diff            # unstaged
   git diff --cached   # already staged
   ```
   List untracked files separately and ask which belong in the commits. Never assume.

2. **Plan the commits.** Group changes into the smallest set of logical, self-contained units.
   Present the plan as a numbered list and ask for approval or edits:
   ```
   Proposed commits (in order):
   1. refactor(auth): extract token parser into its own module
      - src/auth/token-parser.ts (new), src/auth/session.ts
   2. feat(auth): add refresh-token flow
      - src/auth/refresh.ts, src/auth/session.ts (hunks: refresh handling)
   3. test(auth): cover refresh-token expiry
      - src/auth/refresh.spec.ts
   ```
   Ordering: refactors and moves first, then the behaviour change that depends on them, then
   tests/docs for that change (or keep tests with their feature commit if they'd fail alone).
   Prefer each commit leaving the build green.

3. **Stage one commit at a time**
   - Default: file-level. `git add -- <file1> <file2>`
   - Only when one file mixes unrelated changes: hunk-level, by applying a partial patch:
     ```bash
     git diff -- <file> > "${TMPDIR:-/tmp}/full.patch"
     # build ${TMPDIR:-/tmp}/part.patch with only the selected hunks (valid unified diff)
     git apply --cached --check "${TMPDIR:-/tmp}/part.patch" && git apply --cached "${TMPDIR:-/tmp}/part.patch"
     ```
     If it won't apply cleanly, ask the user to stage that file themselves (`git add -p <file>`).
   - **Always** show the result before committing: `git diff --cached --stat` and `git diff --cached`.

4. **Commit** with a message file to keep body and footers intact:
   `git commit -F "${TMPDIR:-/tmp}/commit-msg.txt"`, then show `git log --oneline -1`.

5. **Optional per-commit check.** If the repo declares a fast check, offer to run it after each
   commit so every commit is independently known-good.

6. **Repeat** steps 3–5 per planned commit. Finish with:
   ```bash
   git log --oneline origin/<base>..HEAD
   git status --short   # empty, or only files the user chose to leave out
   ```

7. **Offer to push** (Phase 2) after each batch, so work is backed up and any draft PR stays current.

### Checkpoint mode
"Commit what I've got" mid-feature runs the same flow on the current changes. Small, frequent
commits are the goal; never a single "WIP" commit covering unrelated changes.

### Tidying history
Only on the user's own non-protected branch, and only on request or after offering.
- Fix an earlier commit: stage the fix, `git commit --fixup=<sha>`, then
  ```bash
  git fetch origin
  GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash origin/<base>
  ```
- Reordering or rewording beyond fixups: show the planned todo list to the user first.
- If the branch was already pushed, the tidy requires `git push --force-with-lease`. Say so and
  confirm before pushing.
- On conflicts: stop, show `git status`, help resolve, `git rebase --continue`; offer
  `git rebase --abort` as the way out.

## Phase 2: Push

1. **Run the repo's checks** (stop on failure and show output):
   - "Checks before push" from AGENTS.md, if declared.
   - Otherwise `package.json` scripts if present: a CI-style script (`ci`, `verify`, `check`),
     else `lint`, `typecheck`/`type-check`, `test`. Use the package manager from the lockfile
     (`pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `package-lock.json` → npm, `bun.lockb` → bun).
   - Otherwise a `Makefile` with `lint` / `test` targets.
   - If nothing is declared, say so and continue. Never invent checks.
   - Show the commands before running them. Git hooks also run on their own; never skip them.

2. **Make sure the branch is current with `<base>`**
   ```bash
   git fetch origin
   git log --oneline HEAD..origin/<base>   # commits on base not in this branch
   ```
   If `<base>` has moved, offer `git rebase origin/<base>`. Rebasing an already-pushed branch
   means the next push needs `--force-with-lease` (confirm first).

3. **Show what will be pushed and confirm** (skip the confirmation only under "Push policy: push
   without asking"; still show what was pushed)
   `git log --oneline origin/<branch>..HEAD` (or `origin/<base>..HEAD` on first push).

4. **Push**: first push `git push -u origin <branch>`; after a confirmed rewrite
   `git push --force-with-lease origin <branch>`. Never push to a protected branch.

## Phase 3: Pull request (draft)

Read `references/pr-template.md` before drafting.

1. **Preflight**
   ```bash
   gh auth status
   gh pr view --json url,state 2>/dev/null   # existing PR for this branch?
   ```
   If `gh` is missing or unauthenticated, stop and tell the user (`gh auth login`).
   If a PR exists, offer to update its body instead of creating a new one.

2. **Confirm the base** per the branch model (e.g. task work → the epic's feature branch;
   finished feature → the integration branch). Make sure the base exists on the remote.

3. **Draft** from the branch's commits:
   ```bash
   git log --format='%h %s%n%b' origin/<base>..HEAD
   git diff --stat origin/<base>...HEAD
   ```
   Title in Conventional Commit style; body per `references/pr-template.md`, or the repo's
   `.github/pull_request_template.md` if it has one. Show title and body for approval.

4. **Create**
   ```bash
   gh pr create --draft --base <base> --head <branch> --title "<title>" --body-file "${TMPDIR:-/tmp}/pr-body.md"
   ```
   Report the PR URL.

5. **Merge-method check (warn only).** If the declared merge method keeps individual commits
   (rebase or merge commit) but the repo also allows squash, warn that squashing would collapse
   the atomic commits.

## Reporting back
After each phase: branch, base, commits (`git log --oneline`), what was pushed, PR URL.
Don't recap every command.
