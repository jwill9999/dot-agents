#!/usr/bin/env python3
"""Sync shared MCP servers (~/.agents/mcp/servers.json) into Codex, Claude Code, Cursor and Gemini.

Default is --check: report only, change nothing. --export first refreshes the Docker profile
export (gateway.profile_file) with `docker mcp profile export`; the export is then checked against
the gateway-routed servers. --apply adds what's missing. Existing entries
that differ, and duplicates across routes, are reported; they are only changed with --replace /
--prune. --tool=NAME and --server=NAME (repeatable) limit the run to those tools / servers;
--server skips the Docker profile check. Servers not in servers.json are never touched. No secrets are read from or written to
servers.json; credentials are environment-variable references in each tool's own syntax.
Python 3.9+, standard library only.
"""
import json, os, re, shutil, subprocess, sys, time

HOME = os.path.expanduser("~")
SRC = os.path.join(HOME, ".agents", "mcp", "servers.json")
PATHS = {
    "codex": os.path.join(HOME, ".codex", "config.toml"),
    "claude": os.path.join(HOME, ".claude.json"),
    "cursor": os.path.join(HOME, ".cursor", "mcp.json"),
    "gemini": os.path.join(HOME, ".gemini", "settings.json"),
}
STAMP = time.strftime("%Y%m%d-%H%M%S")
args = set(sys.argv[1:])
APPLY, REPLACE, PRUNE, EXPORT = "--apply" in args, "--replace" in args, "--prune" in args, "--export" in args
ONLY = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--tool=")]
SERVERS = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--server=")]


def expand(p):
    return os.path.expanduser(p) if isinstance(p, str) else p


# ---------- read existing configs ----------
def _toml_value(raw):
    raw = raw.strip()
    if raw in ("true", "false"):
        return raw == "true"
    if raw.startswith("["):
        return [s[1:-1] for s in re.findall(r'"(?:[^"\\]|\\.)*"|\'[^\']*\'', raw)]
    if raw[:1] in "\"'":
        return raw[1:-1]
    return raw


def read_codex(path):
    """Minimal reader for [mcp_servers.<name>] tables (top-level keys only)."""
    out, cur = {}, None
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        m = re.match(r'^\[mcp_servers\.("?)([^".\]]+)\1\]$', s)
        if m:
            cur = m.group(2); out[cur] = {}; continue
        if s.startswith("["):
            cur = None; continue
        if cur and "=" in s and not s.startswith("#"):
            k, v = s.split("=", 1)
            out[cur][k.strip()] = _toml_value(v)
    return out


def read_json_servers(path):
    if not os.path.exists(path):
        return {}
    try:
        return json.load(open(path, encoding="utf-8")).get("mcpServers", {}) or {}
    except Exception as e:
        print("  ! could not parse %s: %s" % (path, e)); return {}


def read(tool):
    return read_codex(PATHS[tool]) if tool == "codex" else read_json_servers(PATHS[tool])


def read_profile_export(path):
    """(profile id, server names) from a `docker mcp profile export` YAML; stdlib only."""
    pid, names, in_server = None, [], False
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^id:\s*(\S+)", line)
        if m:
            pid = m.group(1)
        if line.rstrip() == "        server:":
            in_server = True; continue
        m = re.match(r"^            name:\s*(\S+)", line)
        if in_server and m:
            names.append(m.group(1)); in_server = False
    return pid, names


def check_profile(cfg, gw_servers):
    """Compare the exported Docker profile with the gateway-routed servers; returns problem labels."""
    gw = cfg["gateway"]
    path = os.path.join(os.path.dirname(SRC), gw.get("profile_file", "docker-profile-%s.yaml" % gw["profile"]))
    if EXPORT:
        run_cli(["docker", "mcp", "profile", "export", gw["profile"], path])
    print("\n[docker profile] %s" % path)
    if not os.path.exists(path):
        print("  - no export; run with --export (or: docker mcp profile export %s %s)" % (gw["profile"], path))
        return ["docker profile: no export"]
    pid, names = read_profile_export(path)
    problems = []
    if pid != gw["profile"]:
        print("  ! export is of profile '%s' but the gateway runs '%s'" % (pid, gw["profile"])); problems.append("docker profile: export is of '%s'" % pid)
    lower = {n.lower(): n for n in names}
    claimed = set()
    for name in gw_servers:
        s = cfg["servers"][name]
        hit = [lower[a.lower()] for a in [name] + s.get("aliases", []) if a.lower() in lower]
        if hit:
            claimed.update(hit); print("  ✓ %s%s" % (name, "" if hit[0] == name else " (as %s)" % hit[0]))
        else:
            print("  + missing from profile: %s  (docker mcp profile server ...)" % name); problems.append("docker profile: %s missing" % name)
    for n in names:
        if n not in claimed:
            print("  ? %s is in the profile but not in servers.json" % n); problems.append("docker profile: %s not in servers.json" % n)
    return problems


# ---------- desired state ----------
def desired(cfg, tool):
    skip = set(cfg["tools"].get(tool, {}).get("skip", []))
    want, gateway_needed, connectors = {}, False, []
    for name, s in cfg["servers"].items():
        if name in skip or (SERVERS and name not in SERVERS):
            continue
        if tool in s.get("connector_in", []):
            connectors.append(name); continue
        if s["route"] == "gateway":
            gateway_needed = True
        elif s["route"] == "direct":
            want[name] = dict(s, **s.get("tool_overrides", {}).get(tool, {}))
    if gateway_needed:
        g = cfg["gateway"]
        want[g["name"]] = {"route": "direct", "type": "stdio", "command": g["command"], "args": g["args"], "_gateway": True}
    return want, connectors


def shape(entry):
    """Normalise an existing entry to (kind, target, args, enabled)."""
    url = entry.get("url") or entry.get("httpUrl") or entry.get("serverUrl")
    enabled = entry.get("enabled", True) is not False and entry.get("disabled", False) is not True
    if url:
        return ("http", url, [], enabled)
    return ("stdio", expand(entry.get("command", "")), list(entry.get("args", []) or []), enabled)


def matches(name, s, ename, entry):
    if ename.lower() == name.lower() or ename.lower() in [a.lower() for a in s.get("aliases", [])]:
        return True
    kind, target, eargs, _ = shape(entry)
    blob = " ".join([str(target)] + [str(a) for a in eargs])
    return any(u in blob for u in s.get("match_urls", []) + s.get("match_commands", []))


def same(s, entry):
    kind, target, eargs, enabled = shape(entry)
    if s.get("type", "stdio") == "http":
        return kind == "http" and target.rstrip("/") == s["url"].rstrip("/")
    return kind == "stdio" and os.path.basename(target) == os.path.basename(expand(s["command"])) and eargs == s.get("args", [])


# ---------- per-tool entry formats ----------
def entry_for(tool, s):
    http = s.get("type", "stdio") == "http"
    env = {k: v for k, v in (s.get("env") or {}).items()}
    for k, var in (s.get("env_refs") or {}).items():
        env[k] = {"claude": "${%s}", "cursor": "${env:%s}", "gemini": "${%s}", "codex": "%s"}[tool] % var
    bearer = s.get("bearer_env")
    hdr = s.get("headers_env") or {}  # header name -> env var holding the full header value
    if tool == "cursor":
        if http:
            e = {"url": s["url"]}
            if bearer: e["headers"] = {"Authorization": "Bearer ${env:%s}" % bearer}
            if hdr: e.setdefault("headers", {}).update({k: "${env:%s}" % v for k, v in hdr.items()})
            return e
        e = {"type": "stdio", "command": expand(s["command"]), "args": s.get("args", [])}
        if env: e["env"] = env
        return e
    if tool == "gemini":
        if http:
            if bearer or hdr: return None  # header env expansion isn't documented for Gemini; use tool_overrides
            return {"httpUrl": s["url"]}
        e = {"command": expand(s["command"]), "args": s.get("args", [])}
        if env: e["env"] = env
        if s.get("disabled_tools"): e["excludeTools"] = s["disabled_tools"]
        return e
    if tool == "claude":
        if http:
            e = {"type": "http", "url": s["url"]}
            if bearer: e["headers"] = {"Authorization": "Bearer ${%s}" % bearer}
            if hdr: e.setdefault("headers", {}).update({k: "${%s}" % v for k, v in hdr.items()})
            return e
        e = {"command": expand(s["command"]), "args": s.get("args", [])}
        if env: e["env"] = env
        return e
    if tool == "codex":
        if http:
            if hdr: return None  # `codex mcp add` has no flag for env_http_headers; edit config.toml
            cmd = ["codex", "mcp", "add", "{name}", "--url", s["url"]]
            if bearer: cmd += ["--bearer-token-env-var", bearer]
            return cmd
        cmd = ["codex", "mcp", "add", "{name}"]
        for k, v in env.items():
            cmd += ["--env", "%s=%s" % (k, v)]
        return cmd + ["--", expand(s["command"])] + s.get("args", [])


# ---------- writers ----------
def backup(path):
    if os.path.exists(path):
        shutil.copy2(path, "%s.pre-agents-%s" % (path, STAMP)); return True
    return False


def write_json(tool, adds, removes):
    path = PATHS[tool]
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    servers = data.setdefault("mcpServers", {})
    for n in removes: servers.pop(n, None)
    for n, e in adds.items(): servers[n] = e
    backup(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2); f.write("\n")
    print("  ✎ wrote %s (backup: .pre-agents-%s)" % (path, STAMP))
    return set(removes), set(adds)


def run_cli(cmd):
    exe = shutil.which(cmd[0])
    printable = " ".join("'%s'" % c if (" " in c or "{" in c) else c for c in cmd)
    if not exe:
        print("  → %s not on PATH; run manually: %s" % (cmd[0], printable)); return False
    r = subprocess.run(cmd, capture_output=True, text=True)
    print("  %s %s" % ("✎" if r.returncode == 0 else "✗", printable))
    if r.returncode: print("    " + (r.stderr or r.stdout).strip()[:300])
    return r.returncode == 0


def apply_cli(tool, adds, removes):
    """Returns (names removed, names added) that the CLI accepted."""
    removed, added = set(), set()
    for n in removes:
        if run_cli(["claude", "mcp", "remove", n, "--scope", "user"] if tool == "claude" else ["codex", "mcp", "remove", n]):
            removed.add(n)
    for n, e in adds.items():
        if tool == "claude":
            ok = run_cli(["claude", "mcp", "add-json", n, "--scope", "user", json.dumps(e)])
        else:
            ok = run_cli([c.replace("{name}", n) for c in e])
        if ok: added.add(n)
    return removed, added


# ---------- main ----------
def main():
    cfg = json.load(open(SRC, encoding="utf-8"))
    unknown = [n for n in SERVERS if n not in cfg["servers"]]
    if unknown:
        sys.exit("Unknown server(s) for --server: %s" % ", ".join(unknown))
    gw = cfg["gateway"]
    print("Source: %s   mode: %s" % (SRC, "apply" if APPLY else "check"))
    gw_servers = [n for n, s in cfg["servers"].items() if s["route"] == "gateway" and (not SERVERS or n in SERVERS)]
    # Every problem is an item: (to-do label, done label, how to fix, names to remove, names to add).
    # It counts as changed only when --apply removed and added all of its names.
    items = [(l, l, "manual", [], []) for l in (check_profile(cfg, gw_servers) if gw_servers and not ONLY and not SERVERS else [])]
    changed = []
    for tool in (ONLY or ["codex", "claude", "cursor", "gemini"]):
        path = PATHS[tool]
        print("\n[%s] %s" % (tool, path))
        if not os.path.exists(path) and tool != "claude":
            print("  - config not found; skipping"); continue
        have = read(tool)
        want, connectors = desired(cfg, tool)
        adds, removes, tool_items = {}, [], []
        for name, s in want.items():
            found = [en for en, e in have.items() if matches(name, s, en, e)]
            if not found:
                e = entry_for(tool, s)
                if e is None:
                    print("  ! %s: can't express credentials for %s; configure manually" % (name, tool))
                    tool_items.append(("%s: set up %s by hand" % (tool, name), None, "manual", [], [])); continue
                print("  + missing: %s" % name); adds[name] = e
                tool_items.append(("%s: add %s" % (tool, name), "%s: added %s" % (tool, name), "apply", [], [name])); continue
            en = found[0]; e = have[en]
            kind, target, eargs, enabled = shape(e)
            if not same(s, e):
                print("  ~ differs: %s (have %s %s)" % (en, os.path.basename(str(target)), " ".join(eargs)[:80]))
                tool_items.append(("%s: replace %s" % (tool, en), "%s: replaced %s" % (tool, en), "replace", [en], [name]))
                if REPLACE:
                    removes.append(en); adds[name] = entry_for(tool, s)
            elif not enabled:
                print("  ! %s is disabled in %s; enable it there if wanted" % (en, tool))
                tool_items.append(("%s: %s is disabled" % (tool, en), None, "manual", [], []))
            else:
                print("  ✓ %s" % en)
        for name in connectors:
            s = cfg["servers"][name]
            dup = [en for en, e in have.items() if matches(name, s, en, e)]
            print("  · %s via %s's own connector%s" % (name, tool, "" if not dup else "; DUPLICATE direct entry: " + ", ".join(dup)))
            if dup:
                tool_items.append(("%s: remove duplicate %s" % (tool, ", ".join(dup)), "%s: removed duplicate %s" % (tool, ", ".join(dup)), "prune", dup, []))
                if PRUNE: removes += dup
        for name in gw_servers:
            s = cfg["servers"][name]
            if tool in s.get("connector_in", []): continue
            dup = [en for en, e in have.items() if en != gw["name"] and matches(name, s, en, e)]
            if dup:
                print("  ⚠ duplicate: %s is routed via the gateway but also configured directly as %s" % (name, ", ".join(dup)))
                tool_items.append(("%s: remove duplicate %s" % (tool, ", ".join(dup)), "%s: removed duplicate %s" % (tool, ", ".join(dup)), "prune", dup, []))
                if PRUNE: removes += dup
        removed, added = set(), set()
        if APPLY and (adds or removes):
            if tool in ("cursor", "gemini"): removed, added = write_json(tool, adds, removes)
            else: removed, added = apply_cli(tool, adds, removes)
        for it in tool_items:
            _, done, _, rm, add = it
            if (rm or add) and set(rm) <= removed and set(add) <= added:
                changed.append(done)
            else:
                items.append(it)
    summarize(changed, items)


def summarize(changed, remaining):
    print()
    if APPLY:
        print("Changed %d item(s)%s" % (len(changed), ":" if changed else "."))
        for label in changed: print("  ✎ " + label)
    if not remaining:
        print("No differences." if not changed else "Nothing else needs attention."); return
    print("%d item(s) still need attention:" % len(remaining) if APPLY else "%d item(s) need attention:" % len(remaining))
    hints = {"apply": "--apply", "replace": "--replace", "prune": "--prune", "manual": "fix by hand"}
    for todo, _, fix, _, _ in remaining:
        if APPLY and {"apply": True, "replace": REPLACE, "prune": PRUNE}.get(fix): fix = "manual"  # tried and failed
        print("  - %s  (%s)" % (todo, hints[fix]))


if __name__ == "__main__":
    main()
