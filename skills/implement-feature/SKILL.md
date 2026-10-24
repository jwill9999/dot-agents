---
name: implement-feature
description: "Implements an approved feature or fix with meaningful tests, diagnostics and review, within the project's delivery rules. Use when the user asks to build, implement or fix an agreed change, or to execute an approved plan. Fallback: prefer a project-specific implementation skill when one exists."
---

# Implement feature

Use the current project's agent instructions, issue tracker, approved requirements, definition of
done and delivery rules. This portable workflow does not import Agent Platform-specific commands,
Beads schemas, cloud publication destinations or paused prototype controls into other projects.
Prefer an applicable project implementation skill; do not stack two implementation workflows on the
same task. Supporting test or UI-evaluation skills apply only to relevant parts of that workflow.

## Resolve scope and execute

1. Confirm the intended task, dependencies, current source/worktree, destination and actual owner
   authorization. Preserve dirty and unrelated work. Reconcile stale records with delivery evidence.
2. Fill material planning gaps before code changes. Use
   [portable planning](../plan-feature/SKILL.md) when useful; reuse agreed decisions.
   Routine implementation/refinement within an authorized objective needs no new phase grant.
   Clarify changed owner intent, behavior/delivery, reserved actions or required unavailable inputs.
3. Implement the smallest coherent change. Keep shared backend operations usable by their relevant
   UI, API, agent, CLI or voice clients. Preserve permission, privacy and recovery boundaries.
4. Run meaningful affected tests and required project quality gates. Inspect actual failure artifacts
   before changing code or matchers. Repair from evidence; retain failures and disclose doubles,
   skipped/not-run cases and missing prerequisites. Do not expand into unrelated improvements.
5. Obtain source-aware independent review when required or warranted. Delegate only when available
   and authorized. Fix actionable findings and re-review changed semantics. If independent review
   is unavailable, report it pending; a procedural role assignment is not technical tool isolation.

## Use relevant evidence

For journeys claiming backend effects, exercise the appropriate connected application and verify
persisted state or actual effects independently of UI messages. Include a relevant denial/failure
case where prohibited effects must remain absent. Browser-only evidence does not establish native
desktop behavior; external fixtures do not establish live provider behavior.

Use available application diagnostics after meaningful end-to-end testing and before completion.
Record source/build, scenario and correlation identifiers; examine failures, slow steps, waits and
coverage/loss/truncation indicators. Reuse valid evidence until a change invalidates it. Missing
events are not proof an action never occurred, and one slow sample does not establish a cause.
Distinguish facts from hypotheses, fix in-scope defects and record other useful findings in existing
or deduplicated project issues. Do not add an observability platform just because a signal is absent.

For rendered changes or a requested visual review, use [UI evaluation](../evaluate-ui/SKILL.md)
to choose layout, changed-control accessibility or symptom-led frontend investigation. Backend-only
and documentation changes do not automatically require these modules. Required acceptance evidence
remains required; missing diagnostic coverage is a disclosed gap, not an inferred clean result.

## Deliver and verify

Update task records, results and the project handoff with actual passed, failed, skipped, blocked and
not-run outcomes. Follow the project's documentation/mirror requirements where applicable. Commit
and push scoped work with normal hooks, then open the authorized PR/delivery review when requested.

On meaningful hosted refreshes, inspect all expected latest workflows for the actual head, plus
review threads, blocking reviews and actual security findings. Green CI alone is not merge readiness.
Fix actionable feedback alongside pipeline failures; resolve comments only after the source fix or
evidence-backed disposition is present. Requalify source changed after an earlier success.

Merge, release, deploy or delete branches only within explicit existing authority and project rules.
Use exact-head guards when supported, never bypass required checks, and verify actual delivered
revision/tree before task closure or recovery-protected cleanup. Preserve unique/paused/in-use work.
Keep implemented, tested, reviewed, merged and released states distinct.

Stop when the declared definition of done and authorized delivery are verified. Report a precise
external/input blocker if required progress is impossible after useful scoped work; do not endlessly
repeat unchanged failed input or claim completion because time or context is running short.
