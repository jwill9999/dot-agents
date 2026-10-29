---
name: manage-skills
description: Creates, installs, links, renames, removes and audits agent skills on this machine, and adds shared MCP servers that every coding tool picks up through ~/.agents. Use when the user asks to create or install a skill, symlink a skill into a tool, find duplicate or broken skills, asks where skills are stored, wants to add, share, sync or remove a global or user-level MCP server across tools (Claude Code, Codex, Cursor, Gemini), or wants an MCP server set up for a skill.
---

# Manage skills

Keeps agent skills on this machine consistent: one real copy of every shared skill,
symlinks only where a tool can't read the canonical folder, no duplicates, and no
project-specific content in user-level skills.

Always confirm with the user before creating, moving, renaming or deleting anything.

## The layout (source of truth)

| Location | Role |
|---|---|
| `~/.agents/skills/<name>/` | **Canonical home for every shared (user-level) skill.** Real folders only. |
| `~/.claude/skills/<name>` | **Symlink** to `~/.agents/skills/<name>` (Claude Code needs it). |
| `~/.codex/skills/` | Codex-only skills and Codex's own `.system/`. No shared skills, no symlinks. |
| `~/.agents/.skill-lock.json` | Owned by the `npx skills` installer. Never edit by hand. |
| `<repo>/.agents/skills/<name>/` | **Project-level skills**, committed with the repo. |
| `<repo>/.claude/skills/<name>` | Relative symlink `../../.agents/skills/<name>`, committed. |

Codex, Cursor, GitHub Copilot CLI and Gemini CLI read `~/.agents/skills` directly, so they need
**no** symlinks. Details and sources: `references/tool-paths.md`.

`~/.agents` is also a git repo holding other shared setup (see `~/.agents/README.md`):
`AGENTS.md` (personal global instructions, linked into each tool), `git/` (global gitignore,
commit template, hooks with secret scan), `mcp/` (shared MCP servers, `servers.json` + `sync.py`)
and `bootstrap.sh`, which recreates every link and setting. After adding or renaming a shared
skill, re-running `bash ~/.agents/bootstrap.sh` refreshes the Claude Code links.

## Add a shared MCP server

Global MCP servers are defined once in `~/.agents/mcp/servers.json` and written into each
tool by `~/.agents/mcp/sync.py`; never add a global server to one tool by hand only. Follow
`references/mcp-setup.md` (schema, route choice, sync and verification). In short: check the
server's official setup docs, add one entry, run
`python3 ~/.agents/mcp/sync.py --server=<name>` to check, then add `--apply`, and verify with
a real tool call (`scripts/mcp-probe.py`).

## Rules

1. Shared skills go in `~/.agents/skills/<name>/`, nowhere else. Then link for Claude Code:
   `ln -sfn ~/.agents/skills/<name> ~/.claude/skills/<name>`
2. Never put a shared skill in `~/.cursor/skills`, `~/.gemini/skills`, `~/.copilot/skills` or
   `~/.codex/skills`: tools that read several folders show it twice.
3. **User-level skills contain no project-specific content.** No repo names, absolute paths,
   branch names, tracker schemas or stack-specific commands. Those come from the project's
   AGENTS.md at run time, or the skill belongs at project level. See "Portability check".
4. A tool-specific skill goes in that tool's own folder, with no link.
5. Skills listed in `~/.agents/.skill-lock.json`, or imported from an official catalogue (e.g.
   `playwright`, `migrate-to-codex`), keep their upstream name and content, because updates
   overwrite edits. To customise one, copy it under a new name.
6. Never touch `~/.codex/skills/.system/`.
7. Prefer moving to deleting. When removing a skill, also remove its Claude Code link.

## Naming and format (Agent Skills spec, https://agentskills.io)

- **Action style:** `<verb>-<object>`, e.g. `plan-feature`, `critique-plan`, `commit-push-pr`,
  `manage-skills`. No `-skill` suffix, no vague names (`helper`, `utils`, `tools`).
- Folder name = frontmatter `name`: lowercase letters, digits, hyphens; max 64 characters.
- Frontmatter: only `name` and `description`, for portability.
- Description, third person, max 1024 characters: **what** it does, then **"Use when…"** with
  the phrases a user would actually say. Any fallback or exclusion goes last.
- Optional `scripts/`, `references/`, `assets/`, referenced from SKILL.md so they load only
  when needed. Keep SKILL.md focused; move long detail into references.
- If the skill has `agents/openai.yaml` (Codex UI metadata), keep its `display_name` and any
  `$<name>` mention in `default_prompt` in sync with the skill name.

## Create a new skill

Ask these before drafting, in one round where possible:

1. **Purpose and triggers:** what should it do, and what would the user say to invoke it?
2. **Scope:** reusable across repos (user-level, `~/.agents/skills`) or specific to one project
   (project-level, `<repo>/.agents/skills`)? If unsure, run the portability check on a first
   draft and let the result decide.
3. **Dependencies:** which CLIs, MCP servers or project infrastructure does it need (e.g. `gh`,
   `bd`, Playwright)? Each becomes a preflight check with a "what to do if missing" rule.
   MCP setup: `references/mcp-setup.md`.
4. **AGENTS.md wiring:** which project conventions does it read, and should it be listed in the
   repo's AGENTS.md? If the repo has no conventions section, offer the `init-agent-conventions`
   skill. Key names: `~/.agents/skills/init-agent-conventions/references/conventions-schema.md`.

Then:
5. Check the name is free everywhere tools read:
   `ls ~/.agents/skills ~/.claude/skills ~/.codex/skills <repo>/.agents/skills 2>/dev/null`
6. Draft SKILL.md (and any references/scripts). Run the portability check on the draft.
7. Show the draft and the proposed AGENTS.md change (as a diff) for approval.
8. Write the files and link for Claude Code (user-level: rule 1; project-level: relative
   symlink under `<repo>/.claude/skills/`).
9. Run the audit. Tell the user to start a new session in each tool so it loads.

## Portability check

Run on every new draft, and on user-level skills when asked. Scan for: repo or product names,
absolute paths, usernames, branch names (`main`, `staging`, `develop`, `feature/...`), tracker
names and ID formats, spec/doc path conventions, framework or monorepo commands (e.g. `nx`,
`pnpm`), cloud/project IDs, and desktop-shell specifics.

For each hit, choose one:

| Choice | When | How |
|---|---|---|
| **Parameterise** | Same workflow everywhere, values differ | Read the value from AGENTS.md `## Agent workflow conventions`; if missing, detect a default, state it, confirm with the user, and offer to add it to AGENTS.md (diff first) |
| **Preflight** | Depends on tools not every repo has | Check first (`command -v bd`, `.beads/`, `gh auth status`); skip that step or stop with a clear message |
| **Project-level skill** | The workflow only exists in one project | Create it in `<repo>/.agents/skills/` instead |
| **Keep as an example** | Illustrative only | Label it clearly as an example ("e.g. `bd-123`") |

Report each finding and the choice made.

## Install an existing skill
- Via the installer: `npx skills add <owner/repo>` (writes to `~/.agents/skills` and the lock
  file). Then link for Claude Code.
- From a folder or zip: copy into `~/.agents/skills/<name>/`, check the frontmatter name
  matches the folder, link for Claude Code.
- Read SKILL.md and any scripts before installing a third-party skill. Run the portability
  check and report findings, but don't edit installer-managed skills (rule 5).

## Rename a skill
1. Move the folder; update frontmatter `name` and `agents/openai.yaml` if present.
2. Find references in other skills (`grep -rn '<old>' ~/.agents/skills <repo>/.agents/skills`)
   and update them in the same change.
3. Replace the Claude Code link:
   `rm ~/.claude/skills/<old> && ln -sfn ~/.agents/skills/<new> ~/.claude/skills/<new>`
4. List places outside the skills folders the user should search: repo AGENTS.md / CLAUDE.md
   files and `~/.codex/config.toml`.

## Remove a skill
Confirm first. Remove `~/.claude/skills/<name>` (the link), then the folder. For
installer-managed skills use `npx skills remove <name>`. Check no other skill references it.

## Audit
Run `bash ~/.agents/skills/manage-skills/scripts/audit.sh` and report: canonical symlinks,
name mismatches, broken links, missing Claude Code links, duplicates, and real folders in tool
directories. Offer fixes; apply only after approval.
