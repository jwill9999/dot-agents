# Personal agent instructions (all projects, all tools)

<!-- Global file: ~/.agents/AGENTS.md, linked to ~/.codex/AGENTS.md, ~/.claude/CLAUDE.md and
     ~/.gemini/GEMINI.md by ~/.agents/bootstrap.sh. Project AGENTS.md files take precedence.
     Keep this project-agnostic: no repo names, branches, trackers or stack commands. -->

## About me
- Software engineer in the UK. Strongest in TypeScript, Node, Angular and Nx monorepos.

## How to communicate
- UK English.
- Give clear, detailed assessments. When recommending, include the plan and the pros and cons
  I should weigh.
- Back research-based claims with sources I can follow up (links to official docs first).
- Say plainly when something is uncertain or unverified.

## How to work
- The project's AGENTS.md (and anything it links to) overrides these defaults.
- Use the repo's own tooling: package manager from the lockfile, its scripts, hooks and CI.
- Ask before destructive or hard-to-reverse actions (deleting data, rewriting shared history,
  changing global config).
- Never print, log or commit secrets. Reference credentials through environment variables.
- Prefer small, focused changes with tests that prove the behaviour.

## Git
- Conventional Commits; small atomic commits that can be reverted or cherry-picked alone.
- Never commit to, force-push or rewrite protected branches. Use the `commit-push-pr` skill.

## Temporary VM lifecycle
- Default to one agent-owned temporary test VM across the entire task, including delegated
  work. Keep the application's normal VM separate. Additional concurrent test VMs need an
  explicit requirement and agreed limit; do not allocate one per agent by default.
- Reuse an existing suitable test VM and immutable base image. Do not create another full
  disk or VM for each prompt, retry, approval or test step. Identify which writable state
  must be isolated before making a copy.
- Prefer the owner-configured external development storage for bulky retained test artefacts.
  Record real external paths and aliases; if that volume is required but missing, stop rather
  than silently creating replacement disks in the home directory.
- Before launch, record the task owner, purpose, VM/lease identity, helper process identity,
  disk paths and expected teardown boundary. Never record credentials in this inventory.
- Put owned VM and helper shutdown in guaranteed teardown. Confirm they have stopped after
  the test block, including failures and cancellations. If teardown is unconfirmed, stop
  the block and resolve ownership; do not launch a replacement and accumulate environments.
- Retain compact results and necessary failure evidence. Use `maintain-test-storage` to
  retire approved disposable disks and runtimes after review; stopping a VM alone is not
  storage cleanup. Keep unresolved effects and recovery requirements explicit.
- Do not stop an application-owned VM or unrelated service merely to free a test file.
  Instructions guide agent behaviour; a hard concurrency limit must also be enforced by
  the VM launcher and verified with lifecycle tests.

## Test evidence retention
- Keep generated test reports, traces and temporary documents in one task-owned collection,
  with purpose, outcome, retention reason and review trigger in a compact index. Avoid
  scattering exports across Documents and Downloads.
- After the relevant problem is resolved and reviewed, retire redundant reports, repeated
  preflights, temporary drafts and disposable runtime state using `maintain-test-storage`.
  Retain sufficient final results and failure evidence for unresolved investigations.
- Before retiring duplicates, verify the canonical copy and record its location and digest.
  Do not infer that source projects, owner documents, profiles or old files are disposable.
  Review recovery archives separately so cleanup does not create a permanent archive backlog.

## Shared setup (this machine)
- Shared skills live in `~/.agents/skills` (managed with the `manage-skills` skill).
- Repo conventions live in each repo's AGENTS.md (`init-agent-conventions` sets them up).
- `~/.agents` is a git repo; `bash ~/.agents/bootstrap.sh` recreates links and config.
