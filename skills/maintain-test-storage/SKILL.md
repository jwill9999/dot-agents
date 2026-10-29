---
name: maintain-test-storage
description: Audits retained test artefacts and retires explicitly selected, inactive test files and directories after verifying an external recovery archive. Use when test runtimes, disk images or reports accumulate, or after a completed test block. Works across coding clients using a private machine configuration; it does not manage conversations or provider accounts.
---

# Maintain test storage

Use the same deterministic helper for manual and agent-led maintenance. Python 3.11+
and `lsof` are prerequisites. The helper currently targets POSIX hosts; on unsupported
hosts report the missing prerequisite rather than bypassing the activity checks.
Validate helper changes with `python3 scripts/test_storage.py` and
`python3 scripts/test_relocate.py` before using a changed helper on real files.
Resolve script paths relative to this skill's directory, not the project checkout.

## Audit first

Read the owner's private machine configuration: `--config`, `TEST_STORAGE_CONFIG`,
or by default `test-storage/config.json` under the XDG configuration directory
(the user's `.config` directory when XDG is unset). Never infer that a directory is disposable from its age or
name. Configuration must list exact retired files/directories, reasons, allowed roots,
protected paths and an archive destination on another mounted filesystem.

Run:

```sh
python3 scripts/storage.py --inventory
python3 scripts/storage.py
```

The first command measures `inventory_roots` (or allowed roots) without reading file
contents. The second checks the exact retirement candidates and reports eligible,
blocked or absent items, estimated allocation, a plan digest and current free space.
Neither deletes data or stops applications. Inventory can run with the archive
drive disconnected; retirement checks require the configured archive mount.

## Retire authorised candidates

The owner must authorise removal of the exact candidate batch. An existing explicit
authorisation is sufficient within its scope. Otherwise bring the concrete audit
back for review. Do not convert a recurring audit into unattended deletion.

```sh
python3 scripts/storage.py --apply \
  --plan-digest "$REVIEWED_PLAN_DIGEST" --receipt "$RECEIPT_PATH"
```

The helper refuses source repositories, links, common credential/database filenames, configured
protected paths, overlapping candidates and active/open targets. For each eligible
file or directory it creates a complete compressed archive on the configured external
filesystem, verifies every file against SHA-256, checks source stability and
activity again, then removes the local candidate. Failed checks retain the source.
A narrowly reviewed synthetic CI database may be included only with the candidate's
`fixture_databases` map of relative paths to SHA-256 values, independently matched to
its original downloaded CI artefact. Never whitelist a database just by hashing its
current contents. Credential exceptions are not supported. Keep the original-artefact
path, entry and matching digest as provenance alongside the private batch configuration.
Keep the archive and receipt references together. Never stop unrelated processes to make a
candidate eligible. Missing `lsof` or ambiguous checks mean retain.

Reclaim estimates can overcount shared filesystem extents. Report actual free-space
change separately, along with blocked items, failures and retained recovery copies.

## Relocate retained development artefacts

With explicit owner authorisation, retained inactive files/directories can instead be
moved to an external development collection with a symlink at each original path.
Use a separate private batch configuration, the same allowed/protected roots and
mounted external filesystem, and a new `destination` for each candidate strictly
inside `archive_root`. Keep readable groups such as VM runtimes, test evidence and
historical qualification. Do not relocate the entire coding-client home directory.

```sh
python3 scripts/relocate.py --config "$RELOCATION_CONFIG"
python3 scripts/relocate.py --config "$RELOCATION_CONFIG" --apply \
  --plan-digest "$REVIEWED_PLAN_DIGEST" --receipt "$RECEIPT_PATH"
```

The helper verifies the copied contents and source stability with SHA-256 before
linking, journals each stage and restores the original if link creation fails.
If an operation fails, inspect its journal before any retry: a verified external
copy, temporary copy or local recovery directory may remain. Do not bypass a
non-empty destination refusal. Keep receipts/indexes together. Direct database or
profile relocation is outside this helper's scope; credential/database checks apply.

For VM image directories set candidate `activity_paths` to the containing runtime
root. This guards owner processes referencing the runtime rather than an individual
disk path, and is rechecked throughout relocation. Never relocate an open disk or
stop unrelated services to make it eligible. Preserve
independent writable VM disks; identical hashes do not justify sharing one writable
disk via hardlinks. A verified file relocation is not proof that the VM boots from
its new location. Report launch compatibility as unverified until an authorised
launch/build/shutdown check. The external drive must remain mounted while links
are needed. Keep a clear Documents shortcut and human-readable purpose/retention
index; future cleanup must target the real external locations, not follow links.

## Keep evidence purposeful

For each test collection record the task/owner, purpose, exact location, outcome,
retention reason and review trigger in one private index. A report is useful evidence
only when its reason can be explained to the next agent. Prefer one test collection
over scattered Documents/Downloads exports. Keep the smallest sufficient record:
request/scenario, source/build/provider identity, result and necessary failure evidence.
Do not copy credentials or full prompts into the retention index.

After a problem is resolved and its outcome reviewed, retire superseded traces,
preflights, repeated reports and temporary documents. Preserve representative final
qualification and significant failures where they support an unresolved investigation.
Passing CI alone does not establish that a live workflow works. Never delete solely
because an item is old or has a test-like name.

For unresolved evidence, verify a canonical copy and record its SHA-256 and location
before retiring scattered duplicates. Moving a copy is consolidation, not reclaimed
storage; report that distinction. Do not delete an owner project or arbitrary Markdown
file as if it were generated test output. Database/profile state needs its own evidence
and recovery review. Archive retention is a separate decision: record why a recovery
copy remains and when to review it; do not silently accumulate permanent backups.

## Repeat without accumulating another archive backlog

An agent can run audits after test blocks or when storage is low; the owner can run
the same command manually. Scheduling is optional and needs explicit authorisation.
Follow the shared temporary-VM lifecycle policy: one owned test VM per task by default,
including delegated work; reuse it and confirm teardown before starting a replacement.
New test runs should distinguish disposable runtime files from essential evidence,
record their exact ownership, and retire only after review. Keep failed/unresolved
evidence until its outcome is settled. Archive retention is a separate owner choice.

This skill does not prune coding-client sessions, authentication, plugin stores,
application profiles or managed worktrees. Use the relevant client's supported
archive/restore procedure for those. Client-specific instructions belong in a
clearly labelled machine/project policy, not in this shared implementation.
