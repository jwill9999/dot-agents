---
name: verify-e2e-quality
description: "Defines and checks Playwright end-to-end quality gates: Gherkin acceptance scenarios, UI regression coverage and Electron or browser E2E checks as the definition of done for user-facing features. Use when planning, implementing, reviewing or closing a user-facing task that needs E2E acceptance tests or a definition-of-done check."
---

# Playwright Quality Gate

Use this skill to make Playwright the repeatable human-in-the-loop substitute for user-facing work.
The goal is not high coverage by count; it is confidence that the UI behaves as specified and does
not regress adjacent flows.

## Core Rules

- Treat every manual UI finding as a candidate Playwright regression scenario.
- Test user-visible behaviour: roles, labels, text, visible state, navigation, file attachment,
  dialogs, and outcomes. Avoid asserting implementation details such as component names, CSS
  classes, internal state strings, raw ids, or backend paths.
- Prefer Playwright locators by role, label, placeholder, text, and explicit test ids only where a
  user-facing locator is not stable enough.
- Use web-first assertions such as `await expect(locator).toBeVisible()` instead of polling
  `isVisible()` manually.
- Keep each test isolated. It must create or seed its own data and not depend on execution order,
  local app residue, prior sessions, or previous Projects.
- Every task that changes UI behaviour must add or update Playwright coverage before being marked
  done.
- A task is not complete while its Playwright scenarios fail, are skipped without owner approval, or
  only verify APIs instead of the real UI path.

## Task Workflow

1. Read the task spec and Definition of Done.
2. Add a `Gherkin E2E Strategy` section to the task spec before implementation if one is missing.
3. Convert each critical user behaviour into one or more Playwright scenarios.
4. Implement or update Playwright tests alongside the feature fix.
5. Run focused Playwright tests locally.
6. Run broader local gates required by the repo.
7. Open the task PR and monitor GitHub Actions, traces, screenshots, videos, review comments, and
   security/quality scans.
8. Fix failures on the task branch until all required checks are green.
9. Only then close the task in the project's tracker and merge according to the branch model in
   the repo's AGENTS.md (`## Agent workflow conventions`).

## Gherkin E2E Strategy Format

Use this section in every user-facing task spec:

```gherkin
Feature: <user-facing capability>

  Background:
    Given the desktop app is running in a production-like test environment
    And the test has isolated app data

  Scenario: <primary happy path>
    Given <initial visible state>
    When <user action through the UI>
    Then <visible outcome>
    And <regression-sensitive adjacent outcome>

  Scenario: <failure or edge path>
    Given <initial visible state>
    When <user action that fails or cancels>
    Then <clear user-facing response>
    And <no leaked internal state or stale context>
```

Guidelines:

- Write scenarios from the user's perspective.
- Include one happy path, one failure/cancel path, and one regression-adjacent path where relevant.
- Mention required fixtures, native dialog test hooks, app-data isolation, and expected artifacts.
- Tie each scenario back to the Definition of Done.

## Playwright Test Design

For each scenario:

- Use real route/navigation entry points, not private component mounts, unless the task is explicitly
  component-only.
- Click buttons and menu items by accessible name.
- Fill fields by label or placeholder.
- Assert visible copy and UI state.
- Assert absence of confusing state when relevant, for example:
  - no Previous Chat content in a new Chat,
  - no Project sensors in Personal Chat,
  - no host absolute paths in normal UI,
  - no stale attachments after route changes.
- Use deterministic test fixtures for Projects, sessions, branches, files, and model responses.
- Prefer test doubles at external boundaries such as model providers, GitHub, Sonar, or OS-native
  dialogs; do not mock the UI under test.

## Electron And Native Desktop Rules

Use Electron E2E when acceptance depends on desktop behaviour:

- native folder/file picker flows,
- host Project folder binding,
- app data persistence,
- preload/main-process IPC,
- safeStorage or desktop secrets behaviour,
- external/default IDE handoff,
- terminal dock/PTY lifecycle.

Browser-only Playwright can cover route/component behaviour, but it does not prove native desktop
behaviour. For native dialogs, use explicit test hooks or injected picker responses and still assert
the visible user outcome.

## End-to-End Evidence Contract

Before adding tests, map the chosen user journey to existing coverage. Classify tests as component/page, application integration, or full-system end-to-end according to the layers actually exercised. Record which UI, API, persistence, tools, model providers and host/VM boundaries are real, stubbed or unavailable. A tool named Playwright or an E2E filename does not establish coverage depth.

For journeys claiming backend effects, include in the task acceptance criteria:

- The visible action and expected visible outcome, plus an independent backend postcondition such as a durable record, delivered job result or actual file change.
- A relevant negative case: denied, cancelled or failed work must not produce the prohibited effect. Wait for an observable settled state rather than an arbitrary sleep. Verify the effect is absent, not merely that the UI says it was denied.
- Required evidence and how it is captured: correlate UI requests, application events and durable records by available session/run/request/operation identifiers. Account for new identifiers on resume; do not infer ordering or identity from timestamps alone.
- What a pass means and what remains untested, including model doubles, disabled evaluators, fixture command runners and unavailable real infrastructure.

Prefer accessible UI actions and verify backend outcomes through supported read-only APIs or narrowly scoped inspection of disposable test data. Do not replace the application API, approval service or persistence with mocks when those layers are the behavior being assessed. Deterministic doubles at external boundaries are useful, but their success cannot prove live model quality, actual provider compatibility or VM isolation.

Reuse current logs, audit records and test helpers before adding instrumentation. Browser traces capture browser activity; they do not automatically contain backend spans. Explicitly verify artifact capture for manually launched browser/Electron contexts. Save a compact evaluation with expected versus actual behavior, backend evidence, file/data effects, execution mode and missing signals on success and failure, before cleanup. Refresh final snapshots so a pending record is not misreported as the terminal state. Required evidence missing means inconclusive or failed acceptance, never an inferred pass.

Use isolated projects, databases, identities and ports. Keep artifacts scoped and sanitized: exclude credentials and unrelated user content, bound captured data, and keep generated reports outside lint/build input paths. Detailed backend assertions belong where they add confidence to the claimed journey; page-only rendering tests need not manufacture backend coverage. Missing telemetry is a finding to scope, not automatic authorization for a new observability platform.

## CI And Artifacts

- Configure traces on first retry or retain traces on failure.
- Preserve screenshots/videos/traces for failing E2E tests.
- When a CI E2E test fails, inspect the trace or screenshot before changing code.
- Do not accept "green unit tests" as sufficient for a UI task.
- Do not close a task if a relevant E2E test is skipped unless the task spec documents the owner
  approval and follow-up.

## Definition Of Done Addendum

For user-facing work, append this to the task DoD:

- [ ] Gherkin E2E Strategy is present in the task spec.
- [ ] Playwright tests cover the listed Gherkin scenarios.
- [ ] Tests exercise the real UI flow using accessible locators.
- [ ] Tests verify expected visible behaviour and relevant negative/regression states.
- [ ] Focused Playwright tests pass locally.
- [ ] Required CI Playwright jobs pass on the task PR.
- [ ] Failure artifacts are inspected and addressed when tests fail.

## Anti-Patterns

- Testing only API responses for a UI feature.
- Using CSS selectors where role/label/text locators are available.
- Sharing mutable state between tests.
- Depending on existing local app data.
- Making snapshots the only assertion.
- Marking tasks done with "manual test later" when the flow can be automated.
- Hiding broken UI with skipped tests instead of creating a tracked blocker.
