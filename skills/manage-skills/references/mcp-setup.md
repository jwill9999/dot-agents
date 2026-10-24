# Configuring MCP servers a skill depends on

Skills provide instructions; MCP servers supply tools and authentication. A skill declaring a
tool dependency does not prove a connection is configured, authenticated or working.
Configure only the servers the user asked for or a skill genuinely needs; optional tools stay
optional.

## Steps

1. **Check current docs** for the target client and the server. Configuration differs per tool
   and changes over time; don't assume one client's config works in another. For Codex,
   user-level MCP config normally lives in `~/.codex/config.toml` under `[mcp_servers.<name>]`;
   a project `.codex/config.toml` may override it. Plugin-managed servers have their own
   lifecycle; don't duplicate them as standalone entries.
2. **Inspect existing entries without printing secrets.** Reuse a working connection. For an
   approved addition, use the client's supported command (e.g. `codex mcp add`) or a narrow
   config edit; check the CLI's help/version first. Preserve unrelated settings, comments,
   environment references and approval restrictions.
3. **Credentials:** use official transport/launch settings; keep credentials out of skills and
   sample config; prefer environment-variable references or OAuth. The user completes sign-in,
   account and billing decisions. Never copy tokens between clients. Keep a private backup
   before editing config that contains secrets.
4. **Verify and report separately:** configured, authenticated, tools visible, and actually
   verified with a harmless tool call. A config entry or a process starting is not a working
   tool call. If the client needs a restart, say so and record verification as pending.

## Report
Changed server names and verification results (never credentials), or explicitly "no MCP
configuration changed".

References:
- Codex MCP configuration: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- Codex skills: https://learn.chatgpt.com/docs/build-skills
