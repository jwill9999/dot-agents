#!/usr/bin/env bash
# Read-only detection of a repo's agent workflow facts. Prints a report; changes nothing.
# Usage: bash detect.sh [repo-path]   (bash 3.2 compatible for macOS)
set -u
cd "${1:-.}" || exit 1
root=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "Not a git repository"; exit 1; }
cd "$root"
has() { command -v "$1" >/dev/null 2>&1; }
hdr() { echo; echo "## $1"; }

echo "# Agent conventions detection: $root"

hdr "Git"
echo "current_branch: $(git branch --show-current 2>/dev/null)"
echo "remote: $(git remote get-url origin 2>/dev/null || echo none)"
def=""
if has gh && gh auth status >/dev/null 2>&1; then
  def=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null)
  echo "default_branch (GitHub): ${def:-unknown}"
  echo "merge_methods: $(gh repo view --json rebaseMergeAllowed,squashMergeAllowed,mergeCommitAllowed -q 'to_entries|map("\(.key)=\(.value)")|join(" ")' 2>/dev/null || echo unknown)"
  prot=$(gh api "repos/{owner}/{repo}/branches?protected=true" -q '.[].name' 2>/dev/null | tr '\n' ' ')
  echo "protected_branches (GitHub): ${prot:-unknown (no access or none)}"
else
  def=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
  echo "default_branch (local origin/HEAD): ${def:-unknown}"
  echo "merge_methods: unknown (gh not installed or not signed in)"
  echo "protected_branches: unknown (gh not installed or not signed in)"
fi
echo "long_lived_branches_present: $(for b in main master staging develop dev release; do git show-ref --verify --quiet refs/remotes/origin/$b && printf '%s ' $b; done)"
echo "remote_branch_prefixes (count):"
git branch -r 2>/dev/null | grep -v -- '->' | sed 's#^ *origin/##' | grep / | cut -d/ -f1 | sort | uniq -c | sort -rn | head -8 | sed 's/^/  /'

hdr "Tracker"
if [ -d .beads ]; then
  echo "beads_dir: present"
  if has bd; then echo "bd: installed"; echo "sample_issue_ids:"; bd list --limit 3 2>/dev/null | head -3 | sed 's/^/  /'; else echo "bd: not installed"; fi
else echo "beads_dir: absent"; fi
for d in docs/tasks docs/specs specs .specs; do [ -d "$d" ] && echo "spec_dir: $d ($(ls "$d" | wc -l | tr -d ' ') files)"; done

hdr "Checks"
for f in pnpm-lock.yaml yarn.lock package-lock.json bun.lockb bun.lock; do [ -f "$f" ] && echo "lockfile: $f"; done
if [ -f package.json ] && has node; then
  echo "package_scripts: $(node -e 'try{console.log(Object.keys(require("./package.json").scripts||{}).join(" "))}catch(e){}')"
fi
[ -f Makefile ] && echo "make_targets: $(grep -oE '^[A-Za-z0-9_.-]+:' Makefile | tr -d ':' | sort -u | head -20 | tr '\n' ' ')"
for h in .husky/pre-commit .husky/pre-push .husky/commit-msg lefthook.yml .lefthook.yml .pre-commit-config.yaml; do [ -f "$h" ] && echo "hook: $h"; done
[ -d .github/workflows ] && echo "ci_workflows: $(ls .github/workflows | tr '\n' ' ')"
for t in .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE.md; do [ -f "$t" ] && echo "pr_template: $t"; done

hdr "Instruction files"
if [ -f AGENTS.md ]; then
  echo "AGENTS.md: present ($(wc -l < AGENTS.md | tr -d ' ') lines)"
  grep -q '^## Agent workflow conventions' AGENTS.md && echo "  conventions_section: present" || echo "  conventions_section: missing"
  grep -q '^## Skills used in this repo' AGENTS.md && echo "  skills_section: present" || echo "  skills_section: missing"
  grep -oE '\]\(([^)]+\.md)\)' AGENTS.md | sed 's/](\(.*\))/\1/' | sed 's/^/  links_to: /'
else echo "AGENTS.md: absent"; fi
if [ -f CLAUDE.md ]; then
  echo "CLAUDE.md: present ($(wc -l < CLAUDE.md | tr -d ' ') lines)"
  grep -q '^@AGENTS.md' CLAUDE.md && echo "  imports_AGENTS.md: yes" || echo "  imports_AGENTS.md: no"
else echo "CLAUDE.md: absent"; fi
for f in .github/copilot-instructions.md GEMINI.md .cursorrules .windsurfrules; do [ -f "$f" ] && echo "other_instructions: $f"; done
for d in .github/instructions .cursor/rules .windsurf/rules; do [ -d "$d" ] && echo "other_instructions_dir: $d ($(ls "$d" | tr '\n' ' '))"; done

hdr "Project skills"
for s in .agents/skills/*/; do [ -f "$s/SKILL.md" ] && echo "agents_skill: $(basename "$s")"; done 2>/dev/null
for s in .agents/skills/*/; do [ -d "$s" ] && [ ! -f "$s/SKILL.md" ] && echo "agents_dir_without_SKILL.md (not discovered): $(basename "$s")"; done 2>/dev/null
if [ -d .claude/skills ]; then
  for s in .claude/skills/*; do [ -e "$s" ] || [ -L "$s" ] || continue
    if [ -L "$s" ]; then echo "claude_skill_link: $(basename "$s") -> $(readlink "$s")$( [ -e "$s" ] || echo ' (BROKEN)')"; else echo "claude_skill_real: $(basename "$s")"; fi
  done
else echo ".claude/skills: absent"; fi
for s in .agents/skills/*/; do [ -f "$s/SKILL.md" ] || continue; n=$(basename "$s"); [ -e ".claude/skills/$n" ] || echo "missing_claude_link: $n"; done 2>/dev/null
[ -d .github/skills ] && echo "github_skills_dir: $(ls .github/skills | tr '\n' ' ')"

hdr "Hints"
grep -rniE 'never say .?ready to push|work is not complete until .?git push|must push' AGENTS.md CLAUDE.md docs/*.md 2>/dev/null | head -3 | sed 's/^/push_rule: /'
grep -rniE 'broker|autonomous run' AGENTS.md docs/agent-instructions*.md 2>/dev/null | head -2 | sed 's/^/autonomous_rule: /'
exit 0
