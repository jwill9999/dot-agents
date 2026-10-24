# Personal agent instructions (all projects, all tools)

<!-- Global file: ~/.agents/AGENTS.md, linked to ~/.codex/AGENTS.md, ~/.claude/CLAUDE.md and
     ~/.gemini/GEMINI.md by ~/.agents/bootstrap.sh. Project AGENTS.md files take precedence.
     Keep this project-agnostic: no repo names, branches, trackers or stack commands. -->

## About me
- Software engineer in the UK. Strongest in TypeScript, Node, Angular and Nx monorepos.

## How to communicate
- UK English.
- Give clear, detailed assessments. When recommending, include the plan and the pros and cons
  I should weigh.
- Back research-based claims with sources I can follow up (links to official docs first).
- Say plainly when something is uncertain or unverified.

## How to work
- The project's AGENTS.md (and anything it links to) overrides these defaults.
- Use the repo's own tooling: package manager from the lockfile, its scripts, hooks and CI.
- Ask before destructive or hard-to-reverse actions (deleting data, rewriting shared history,
  changing global config).
- Never print, log or commit secrets. Reference credentials through environment variables.
- Prefer small, focused changes with tests that prove the behaviour.

## Git
- Conventional Commits; small atomic commits that can be reverted or cherry-picked alone.
- Never commit to, force-push or rewrite protected branches. Use the `commit-push-pr` skill.

## Shared setup (this machine)
- Shared skills live in `~/.agents/skills` (managed with the `manage-skills` skill).
- Repo conventions live in each repo's AGENTS.md (`init-agent-conventions` sets them up).
- `~/.agents` is a git repo; `bash ~/.agents/bootstrap.sh` recreates links and config.
