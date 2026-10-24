# Where each tool reads skills (verified 2026-10-24)

Re-check these docs when a tool updates; locations change.

| Tool | User-level folders | Notes |
|---|---|---|
| Codex | `~/.agents/skills` | Follows symlinks. Same-named skills are not merged; both appear. Docs no longer mention `~/.codex/skills`. Disable a skill in `~/.codex/config.toml`. https://learn.chatgpt.com/docs/build-skills.md |
| Cursor | `~/.agents/skills`, `~/.cursor/skills`, `~/.claude/skills`, `~/.codex/skills` | Reads all four, so a skill in two of them may appear twice. https://cursor.com/docs/skills |
| GitHub Copilot CLI | `~/.copilot/skills`, `~/.agents/skills` | https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills |
| Gemini CLI | `~/.gemini/skills`, `~/.agents/skills` | `~/.agents` wins on name clash; workspace `.gemini/skills` or `.agents/skills` override user skills. https://geminicli.com/docs/cli/skills/ |
| Claude Code | `~/.claude/skills` | Not confirmed to read `~/.agents/skills`, hence the per-skill symlinks. |

Spec: https://agentskills.io
