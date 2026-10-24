#!/usr/bin/env bash
# Recreate the shared agent setup on this machine from ~/.agents. Idempotent and safe to re-run.
# Usage: bash ~/.agents/bootstrap.sh [--dry-run] [--mcp-apply]
# macOS bash 3.2 compatible.
set -u
A="$HOME/.agents"
DRY=0; MCP_MODE="--check"
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --mcp-apply) MCP_MODE="--apply" ;;
    -h|--help) sed -n '2,4p' "$0"; exit 0 ;;
  esac
done
STAMP=$(date +%Y%m%d-%H%M%S)
run() { if [ $DRY -eq 1 ]; then echo "  [dry-run] $*"; else eval "$@"; fi; }
say() { echo "$*"; }

# Link $1 (source) to $2 (target). Backs up a non-empty real file; replaces an empty one.
link() {
  src="$1"; dst="$2"
  [ -e "$src" ] || { say "  - skip $dst (source $src missing)"; return; }
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then say "  ✓ $dst"; return; fi
  run "mkdir -p \"$(dirname "$dst")\""
  if [ -L "$dst" ]; then run "rm \"$dst\""
  elif [ -e "$dst" ]; then
    if [ -s "$dst" ]; then say "  ! $dst exists with content; backing up to $dst.pre-agents-$STAMP (merge it into $src)"; run "mv \"$dst\" \"$dst.pre-agents-$STAMP\""
    else run "rm \"$dst\""; fi
  fi
  run "ln -s \"$src\" \"$dst\""; say "  + $dst -> $src"
}

# Set a global git config key only if unset or already ours.
git_set() {
  key="$1"; val="$2"; cur=$(git config --global --get "$key" 2>/dev/null)
  if [ "$cur" = "$val" ]; then say "  ✓ git $key"; return; fi
  if [ -n "$cur" ]; then say "  ! git $key is already '$cur'; left unchanged (set it to $val manually if wanted)"; return; fi
  run "git config --global \"$key\" \"$val\""; say "  + git $key = $val"
}

say "1. Claude Code skill links (other tools read ~/.agents/skills directly)"
for p in "$A"/skills/*/; do n=$(basename "$p"); link "${p%/}" "$HOME/.claude/skills/$n"; done
for l in "$HOME"/.claude/skills/*; do
  if [ -L "$l" ] && [ ! -e "$l" ]; then say "  - removing broken link $l"; run "rm \"$l\""; fi
done

say "2. Global instructions (one file, linked into each tool)"
link "$A/AGENTS.md" "$HOME/.codex/AGENTS.md"
link "$A/AGENTS.md" "$HOME/.claude/CLAUDE.md"
link "$A/AGENTS.md" "$HOME/.gemini/GEMINI.md"

say "3. Global git"
git_set core.excludesFile "$A/git/gitignore_global"
git_set commit.template "$A/git/gitmessage"
git_set core.hooksPath "$A/git/hooks"
command -v gitleaks >/dev/null 2>&1 && say "  ✓ gitleaks installed" || say "  ! gitleaks not installed: brew install gitleaks"

say "4. MCP servers ($MCP_MODE)"
if [ -f "$A/mcp/sync.py" ]; then
  if [ $DRY -eq 1 ] && [ "$MCP_MODE" = "--apply" ]; then say "  [dry-run] python3 $A/mcp/sync.py --apply"
  else python3 "$A/mcp/sync.py" $MCP_MODE; fi
else say "  - mcp/sync.py not set up yet"; fi

say "5. Audit"
bash "$A/skills/manage-skills/scripts/audit.sh"
