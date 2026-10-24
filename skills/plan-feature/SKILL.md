---
name: plan-feature
description: "Produces a bounded, source-backed implementation plan for a feature, fix or refactor, following the project's tracker and verification conventions. Use when the user asks to plan a feature, scope a change, write an implementation plan, break work into tasks, or prepare a handoff before coding. Fallback: prefer a project-specific planning skill when one exists."
---

# Plan feature

Produce a reviewable implementation handoff, scaled to the actual change. Read the project's agent
instructions and use its existing issue tracker, specification locations and branch/delivery rules.
Prefer an applicable project-specific planning skill over this fallback; do not run both planning
workflows for the same task unless explicitly requested.
Do not impose another project's Beads schema, Notion destinations, runtime stack or merge policy.
A planning-only request remains planning; reuse existing owner authorization without inventing it.

## Establish the bounded change

Resolve the owner's request against existing tasks, plans, decisions and the smallest useful current
source/test set. Identify what is already implemented, actual gaps and stale task assumptions.
Preserve unrelated work. Record the source revision/worktree used; a proposed branch is not an
existing branch. Ask only about unresolved choices that materially affect scope, behavior, delivery
or a reserved action. Do not treat silence as agreement on those choices.

Define objective, testable requirements, non-goals, acceptance criteria, affected interfaces/files,
dependencies and an explicit stopping point. Give a rough effort range with assumptions and a
checkpoint for reducing scope if uncertainty grows. For an MVP, defer optional infrastructure and
broader redesign unless required to answer the agreed acceptance questions.

Identify all relevant clients: UI, API, agent tools, CLI or voice. Put shared execution, permissions
and durable state in the appropriate common layer; do not assume a button is the only interface.
Describe architecture changes only where the proposal needs them.

## Make verification feasible before promising it

For each requirement record the meaningful unit, integration and connected journey coverage:
inputs/actions, expected outcome, independently checked persisted state or effects, negative case,
environment/data, evidence and owning task. Mark omitted layers with an applicability reason.
Choose tools that fit the project; do not require browser tests for a backend-only change.

For user-facing/backend-effect claims, specify an actual connected journey and an independent
postcondition. UI text or an HTTP success alone is insufficient. Disclose external doubles and what
they cannot prove. Include relevant errors, denial, cancellation/retry or recovery cases; do not
mechanically add every edge case to every feature.

Check service/host/runner access, disposable data/reset, credentials availability without reading
secrets, and permitted costs. Give required missing prerequisites an owner and dependency. Do not
claim readiness where required testing has no feasible environment. Assign a final integration
check across tasks when the feature is split; it must not disappear between individual sign-offs.

## Hand off a complete plan

Maintain one linked plan/manifest rather than a second backlog. Use the project's actual document
locations. Include:

- Requirements, exclusions, decisions and owner authorization boundaries.
- Real task identities, dependency order, responsibilities and source/branch/delivery mapping.
- Task boundaries and definitions of done aligned with the issue tracker.
- Verification scenarios, prerequisites, evidence and final integration ownership.
- Effort/uncertainty, stopping conditions and questions that still require a decision.

Obtain a distinct source-aware critique when required by the task/project or warranted by substantive
risk. Use [portable plan critique](../critique-plan/SKILL.md) when available. Delegation
requires actual session authorization; otherwise record independent review as pending. Fix and
recheck actionable findings; never describe self-review as independent approval.

Validate document links, task/dependency alignment and required publication/readbacks. Separate
planned tests from eventual results. Present the bounded plan if owner acceptance is outstanding;
otherwise continue through [portable implementation](../implement-feature/SKILL.md)
within existing authorization. Plan publication, a critique or passing checks alone grants no
additional merge, deployment, spending or external-action authority.
