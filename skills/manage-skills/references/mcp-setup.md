# Configuring MCP servers

Skills provide instructions; MCP servers supply tools and authentication. A skill declaring a
tool dependency does not prove a connection is configured, authenticated or working.
Configure only the servers the user asked for or a skill genuinely needs; optional tools stay
optional.

## Shared servers: `~/.agents/mcp`

A user-level ("global") server is defined once in `~/.agents/mcp/servers.json`.
`~/.agents/mcp/sync.py` writes it into Codex (`~/.codex/config.toml`), Claude Code
(`~/.claude.json`, user scope), Cursor (`~/.cursor/mcp.json`) and Gemini
(`~/.gemini/settings.json`), each in its own format. `bash ~/.agents/bootstrap.sh` runs the
sync in check mode; `--mcp-apply` applies it.

### Pick one route

| Route | Use when | Effect |
|---|---|---|
| `direct` | A local stdio command or a remote HTTP URL each tool can run itself | Written into every tool |
| `gateway` | The server runs in the Docker MCP gateway profile (`gateway.profile`) | Tools get one `MCP_DOCKER` entry; add the server to the Docker profile too |
| `connector` | Not used as a route on its own; list tools in `connector_in` instead | Those tools use their built-in connection; sync flags duplicate direct entries |

### Entry fields

```jsonc
"<name>": {
  "route": "direct",                 // direct | gateway
  "type": "stdio",                   // stdio (command/args) or http (url)
  "command": "npx",                  // stdio only; ~ is expanded
  "args": ["-y", "<package>@latest"],
  "url": "https://…/mcp",            // http only
  "env": {"KEY": "non-secret value"},
  "env_refs": {"KEY": "ENV_VAR_NAME"},  // secrets: variable NAME only, rendered per tool
  "bearer_env": "ENV_VAR_NAME",      // http bearer token from an env var
  "headers_env": {"Authorization": "ENV_VAR_NAME"},  // http header whose full value is in an env var (e.g. "Basic …"); Codex/Gemini need a hand edit or tool_overrides
  "tool_overrides": {"gemini": {…}},  // per-tool replacement fields, e.g. an mcp-remote stdio wrapper
  "disabled_tools": ["toolName"],      // tools to block: Gemini excludeTools is written by sync; Codex disabled_tools, Claude Code permissions.deny and Cursor toggles are set by hand
  "aliases": ["other-name"],         // names the server already has in some tool
  "match_commands": ["<package>"],   // or match_urls: spot existing entries under other names
  "connector_in": ["codex"],         // tools that use their own built-in connection
  "note": "What it is, prerequisites, sign-in."
}
```

`tools.<tool>.skip` lists servers a tool should not get. Use the server's documented name
(e.g. `mastra` for `@mastra/mcp-docs-server`), and add the other names it is known by as
`aliases` so existing entries are recognised rather than duplicated.

### Steps

1. **Check the official setup docs** for the server (command, args, transport, env vars,
   runtime requirements such as a minimum Node version) and confirm the local runtime meets
   them. Prefer the local stdio form unless the user wants a hosted one.
2. **Inspect without printing secrets.** Run `python3 ~/.agents/mcp/sync.py` (check mode)
   and note anything already pending. A plain `--apply` also applies those pending items, so
   scope the run with `--server=<name>` (and `--tool=<tool>` if needed) unless the user wants
   everything synced.
3. **Add the entry** to `servers.json` with a narrow edit that keeps the file's formatting.
4. **Check, then apply:** `python3 ~/.agents/mcp/sync.py --server=<name>`, then the same with
   `--apply`. Cursor and Gemini files are backed up as `*.pre-agents-<stamp>`; Claude Code
   and Codex go through their CLIs (`claude mcp add-json --scope user`, `codex mcp add`).
5. **If a client CLI fails** (e.g. an old `codex` without `mcp add`, or one that can't parse
   existing entries), back up the config file, make a narrow edit in that tool's documented
   format, and re-run the check until it reports `✓`. Tell the user about the old CLI rather
   than upgrading it unasked.
6. **Verify** (see below) and commit `servers.json` in `~/.agents` with Conventional Commits,
   staging only the files you changed.

## Per-tool or project-only servers

For a server one tool or one repo needs, use that client's supported command or config file
instead (e.g. `claude mcp add --scope project`, a project `.codex/config.toml`). Check current
docs: configuration differs per tool and changes over time. Plugin-managed servers have their
own lifecycle; don't duplicate them as standalone entries.

## Credentials

Use official transport/launch settings; keep credentials out of skills, `servers.json` and
sample config; prefer environment-variable references (`env_refs`, `bearer_env`) or OAuth.
The user completes sign-in, account and billing decisions. Never copy tokens between
clients. Keep a private backup before editing config that contains secrets, and never print
those files.

## Verify and report separately

Configured, authenticated, tools visible, and actually verified with a harmless tool call:

- `python3 ~/.agents/skills/manage-skills/scripts/mcp-probe.py -- <command> <args…>` starts
  a stdio server, lists its tools and, with `--call <tool> --args '<json>'`, makes one call.
- `claude mcp get <name>` shows Claude Code's connection status.

A config entry or a process starting is not a working tool call. Running sessions only see a
new server after a restart; say so and record in-tool verification as pending.

## Report
Changed server names, the tools each was written to, any hand edits and backups, and
verification results (never credentials), or explicitly "no MCP configuration changed".

References:
- Claude Code MCP: https://docs.claude.com/en/docs/claude-code/mcp
- Codex MCP configuration: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- Cursor MCP: https://cursor.com/docs/context/mcp
- Gemini CLI MCP: https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md
- Codex skills: https://learn.chatgpt.com/docs/build-skills
