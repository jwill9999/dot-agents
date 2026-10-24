# ~/.agents: shared agent setup

One home for everything shared across projects and agent tools (Claude Code, Codex, Cursor,
GitHub Copilot CLI, Gemini CLI). Versioned in git; `bootstrap.sh` wires it into each tool.

## Layout

| Path | What | Shared how |
|---|---|---|
| `skills/` | Agent Skills (https://agentskills.io) | Codex, Cursor, Copilot CLI and Gemini read it directly; Claude Code via `~/.claude/skills/<name>` links |
| `AGENTS.md` | Personal, project-agnostic instructions | Linked to `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md` |
| `git/gitignore_global` | Never-commit patterns | `git config --global core.excludesFile` |
| `git/gitmessage` | Conventional Commit template | `git config --global commit.template` |
| `git/hooks/` | Global hooks: secret scan (gitleaks), then the repo's own `.git/hooks/*` | `git config --global core.hooksPath` |
| `mcp/servers.json` | Shared MCP server definitions | `mcp/sync.py` writes each tool's own config format |
| `.skill-lock.json` | `npx skills` installer state | Managed by the installer; don't hand-edit |

## Set up a machine

```bash
git clone <this repo> ~/.agents
bash ~/.agents/bootstrap.sh --dry-run   # preview
bash ~/.agents/bootstrap.sh             # apply (MCP sync in check mode)
bash ~/.agents/bootstrap.sh --mcp-apply # also write MCP config to each tool
brew install gitleaks
```

Bootstrap is idempotent. It never overwrites existing content: a non-empty file at a link
target is backed up as `<file>.pre-agents-<timestamp>`, and existing global git settings are
reported, not replaced.

## Rules
- No secrets in this repo. MCP credentials are environment-variable references only.
- New shared skill: create in `skills/`, then re-run bootstrap (or use `manage-skills`).
- Repos using husky set their own hooks path, so global hooks don't run there. To add the
  secret scan, put this line in `.husky/pre-commit`:
  `[ -x "$HOME/.agents/git/hooks/secret-scan.sh" ] && "$HOME/.agents/git/hooks/secret-scan.sh"`
- Some hook installers refuse to run, or write into the global hooks folder, while
  `core.hooksPath` is set globally (e.g. the pre-commit framework). If one complains, run it
  with a repo-local `git config core.hooksPath .git/hooks`, which the dispatcher then
  doesn't affect.
