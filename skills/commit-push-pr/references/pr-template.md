# Pull request template

Use this when the repo has no `.github/pull_request_template.md`.
If the repo has its own template, fill that instead and carry the same information into it.

## Title

Conventional Commit style, summarising the branch as a whole:

```
<type>(<scope>): <summary>
```

e.g. `feat(auth): token refresh flow`

## Body

```markdown
## Summary
<!-- 1–3 sentences: what this PR does and why. -->

## Commits
<!-- One line per commit, in order. Each is atomic and can be reverted or
     cherry-picked on its own. -->
- `<sha>` <type>(<scope>): <subject>
- `<sha>` <type>(<scope>): <subject>

## Changes
<!-- Notable changes grouped by area. Call out anything reviewers should look
     at closely: public API changes, migrations, config, security-sensitive code. -->

## Testing
<!-- What was run and the result. Use the checks actually executed in the
     Push phase; do not claim checks that were not run. -->
- [x] `<command>`: passed
- [ ] Manual testing: <describe or "not done">

## Breaking changes
<!-- "None", or describe impact and migration steps. -->

## Related
<!-- Tracker issue if the repo uses one, plus links to related PRs or docs. -->
Refs: <issue-id>

## Merge
<!-- From AGENTS.md "Merge method". Omit if not declared. -->
Merge with **<merge method>** into `<base>`.
```

## Rules

- Only list checks that were actually run; leave unchecked boxes for anything not done.
- Omit the "Breaking changes" and "Related" sections if empty, except keep "Breaking changes: None"
  when the PR touches a public API.
- If the merge method is rebase and merge, note that it creates new commit SHAs on the base
  branch; cherry-pick later using those SHAs, not the ones listed in this PR body.
