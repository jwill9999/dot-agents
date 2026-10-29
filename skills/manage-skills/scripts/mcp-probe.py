#!/usr/bin/env python3
"""Start a stdio MCP server, list its tools and optionally make one tool call.

Usage: mcp-probe.py [--call TOOL --args JSON] [--timeout SECONDS] -- COMMAND [ARGS...]
Example: mcp-probe.py --call mastraDocs --args '{"paths":["reference/agents/"]}' \
           -- npx -y @mastra/mcp-docs-server@latest
Exits non-zero if the handshake, listing or call fails. Python 3.9+, standard library only.
"""
import argparse, json, select, subprocess, sys, time

ap = argparse.ArgumentParser()
ap.add_argument("--call")
ap.add_argument("--args", default="{}")
ap.add_argument("--timeout", type=int, default=120)
ap.add_argument("command", nargs=argparse.REMAINDER)
opt = ap.parse_args()
cmd = opt.command[1:] if opt.command[:1] == ["--"] else opt.command
if not cmd:
    ap.error("give the server command after --")

p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)


def send(msg):
    p.stdin.write(json.dumps(msg) + "\n"); p.stdin.flush()


def recv(i):
    end = time.time() + opt.timeout
    while time.time() < end:
        if select.select([p.stdout], [], [], 1)[0]:
            line = p.stdout.readline()
            if not line:
                break
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg.get("id") == i:
                if "error" in msg:
                    sys.exit("error: %s" % msg["error"])
                return msg["result"]
    sys.exit("no response to request %s (timeout or server exited)" % i)


try:
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "mcp-probe", "version": "1"}}})
    print("server:", recv(1).get("serverInfo"))
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    print("tools:", ", ".join(t["name"] for t in recv(2)["tools"]))
    if opt.call:
        send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": opt.call, "arguments": json.loads(opt.args)}})
        res = recv(3)
        text = " ".join(c.get("text", "") for c in res.get("content", []))
        print("call %s: %s" % ("FAILED" if res.get("isError") else "ok", text[:300].replace("\n", " ")))
        if res.get("isError"):
            sys.exit(1)
finally:
    p.terminate()
    try:
        p.wait(10)
    except subprocess.TimeoutExpired:
        p.kill()
