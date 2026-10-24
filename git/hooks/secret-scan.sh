#!/usr/bin/env bash
# Scan staged changes for secrets with gitleaks. Used by the global pre-commit hook and,
# in repos with husky, from .husky/pre-commit. Non-blocking if gitleaks isn't installed.
if ! command -v gitleaks >/dev/null 2>&1; then
  echo "[secret-scan] gitleaks not installed; skipping (brew install gitleaks)" >&2
  exit 0
fi
# gitleaks >= 8.19 uses 'git --pre-commit --staged'; older versions use 'protect --staged'.
if gitleaks git --help >/dev/null 2>&1; then
  gitleaks git --pre-commit --staged --redact --no-banner
else
  gitleaks protect --staged --redact --no-banner
fi
status=$?
if [ $status -ne 0 ]; then
  echo "[secret-scan] Possible secret in staged changes. Remove it, or if it's a false positive add it to .gitleaksignore." >&2
fi
exit $status
