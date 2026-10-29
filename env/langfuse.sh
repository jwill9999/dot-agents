# Langfuse credentials from the macOS Keychain. Sourced by ~/.zshenv; holds no secrets.
#
# Store the keys once (each command prompts for the value, so nothing lands in shell history):
#   security add-generic-password -U -a "$USER" -s langfuse-public-key -w
#   security add-generic-password -U -a "$USER" -s langfuse-secret-key -w
#
# Exports:
#   LANGFUSE_HOST, LANGFUSE_BASE_URL   Langfuse base URL (CLI and SDKs read one or the other)
#   LANGFUSE_PUBLIC_KEY   pk-lf-...
#   LANGFUSE_SECRET_KEY   sk-lf-...
#   LANGFUSE_MCP_AUTH     "Basic <base64(pk:sk)>", the Authorization header for the Langfuse MCP server

export LANGFUSE_HOST="${LANGFUSE_HOST:-${LANGFUSE_BASE_URL:-https://cloud.langfuse.com}}"
export LANGFUSE_BASE_URL="${LANGFUSE_BASE_URL:-$LANGFUSE_HOST}"

# Child shells inherit the values, so only the first shell hits the Keychain.
if [ -z "${LANGFUSE_SECRET_KEY-}" ] && command -v security >/dev/null 2>&1; then
  _lf_pk="$(security find-generic-password -a "$USER" -s langfuse-public-key -w 2>/dev/null)"
  _lf_sk="$(security find-generic-password -a "$USER" -s langfuse-secret-key -w 2>/dev/null)"
  if [ -n "$_lf_pk" ] && [ -n "$_lf_sk" ]; then
    export LANGFUSE_PUBLIC_KEY="$_lf_pk"
    export LANGFUSE_SECRET_KEY="$_lf_sk"
    export LANGFUSE_MCP_AUTH="Basic $(printf '%s:%s' "$_lf_pk" "$_lf_sk" | base64 | tr -d '\n')"
  fi
  unset _lf_pk _lf_sk
fi
