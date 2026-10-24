#!/usr/bin/env bash
# Audit agent skill folders for duplicates, broken links and layout drift.
set -u
A="$HOME/.agents/skills"
TOOLS=("$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.cursor/skills" "$HOME/.gemini/skills" "$HOME/.copilot/skills")
issues=0
say() { echo "  - $*"; issues=$((issues+1)); }

echo "Canonical: $A"
echo "[1] Canonical entries that are symlinks (should be real folders):"
for p in "$A"/*; do [ -L "$p" ] && say "$(basename "$p") -> $(readlink "$p")"; done

echo "[2] Frontmatter name does not match folder:"
for p in "$A"/*/; do
  f="$p/SKILL.md"; d=$(basename "$p")
  [ -f "$f" ] || { say "$d: no SKILL.md"; continue; }
  n=$(sed -n 's/^name:[[:space:]]*//p' "$f" | head -1 | tr -d "\"'")
  [ "$n" = "$d" ] || say "$d: name is '$n'"
done

echo "[3] Broken symlinks in tool folders:"
for t in "${TOOLS[@]}"; do [ -d "$t" ] || continue
  for p in "$t"/*; do [ -L "$p" ] && [ ! -e "$p" ] && say "$p -> $(readlink "$p")"; done
done

echo "[4] Shared skills missing a Claude Code link:"
if [ -d "$HOME/.claude/skills" ]; then
  for p in "$A"/*/; do d=$(basename "$p"); [ -e "$HOME/.claude/skills/$d" ] || say "$d"; done
else echo "  (~/.claude/skills not found)"; fi

echo "[5] Duplicates: same name in ~/.agents/skills and another tool folder (Claude links excluded):"
for t in "${TOOLS[@]:1}"; do [ -d "$t" ] || continue
  for p in "$t"/*; do d=$(basename "$p"); [ -e "$A/$d" ] && say "$d also in $t"; done
done

echo "[6] Real skill folders in tool directories (fine if tool-specific):"
for t in "${TOOLS[@]}"; do [ -d "$t" ] || continue
  for p in "$t"/*/; do [ -L "${p%/}" ] || echo "  * ${p%/}"; done
done

echo; [ $issues -eq 0 ] && echo "No issues found." || echo "$issues issue(s) found."
