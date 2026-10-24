---
name: evaluate-ui
description: "Selects and runs proportionate layout, accessibility and frontend performance checks for a UI change. Use when the user asks to review, audit or check a screen, page or component, or when frontend changes need visual, accessibility or performance evidence. Not for backend-only or documentation changes."
---

# Evaluate UI

Evaluate only evidence that can inform the current change. Follow the project's existing functional
acceptance tests, diagnostic workflow and task tracker. This portable skill adds selective review;
it does not require another skill, a particular framework, an MCP connection or a new test suite.

## Select modules from the change

Inspect the task acceptance criteria, actual diff and affected consumers. Record the selected
modules and a short reason in the existing task/results record; read only the selected references.

| Change or request                                                                                                 | Evaluation to select                                                                                                                                   |
| ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Spacing, typography, colours, panels, responsive layout, or an explicit layout review                             | [Layout](references/layout.md); add accessibility when readability, contrast, size, focus or reading order is affected.                                |
| New or changed interactive controls, modal, keyboard flow, or status announcements                                | Existing functional Playwright checks plus [accessibility](references/accessibility.md) for the changed surface; layout only where appearance changes. |
| Reported UI lag, rendering/layout shift, excessive renderer requests, or an agreed frontend performance criterion | [Frontend investigation](references/frontend-investigation.md) for the reproduced symptom; use backend evidence for backend delays.                    |
| API/backend change with no rendered or interaction effect                                                         | Existing API, persistence and diagnostic checks only. No screenshot, layout or browser performance audit.                                              |
| API change affecting a visible error, loading state or action availability                                        | Focused existing UI journey for that consumer. Add only the modules affected by its visible/interaction change.                                        |
| Native desktop lifecycle, IPC, picker, filesystem or VM behaviour                                                 | Existing desktop-shell (e.g. Electron) and backend gates. Visual modules apply only if the rendered surface also changes.                                                       |
| Documentation-only work                                                                                           | None; document validation applies.                                                                                                                     |

Do not activate every module whenever the app starts or because a file is TSX. Explicit audit
requests can select a wider named surface; routine tasks do not inherit an application-wide audit.
Keep backend operations authoritative for UI, chat, voice and future CLI clients; evaluating a
button does not move execution or permissions into the renderer.

## Collect and use evidence at the right stage

| Stage                                        | Evidence and decision                                                                                                                                                                                                                      |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Scope/reproduction                           | Reuse applicable existing reports/tests; identify the affected state and an observable problem. Capture a before screenshot only when a visual comparison helps. Agree the bounded audit surface before a broader redesign or audit.       |
| After the focused implementation/E2E journey | Review selected screenshots, changed-control accessibility, or the reproduced performance trace. Correlate relevant API/run reports and durable effects; screenshots alone do not prove backend success.                                   |
| Failure investigation                        | Inspect the actual failure artifact before changing code or a test. Separate observed facts from suspected causes; collect the next narrow measurement needed to distinguish them.                                                         |
| Before task completion                       | Reuse evidence matching the tested source, build, scenario and environment. Recapture only evidence invalidated by subsequent changes. Record findings, fixes, retests and remaining coverage gaps alongside existing acceptance evidence. |

Choose a representative journey and relevant edge state, not a new inventory of every screen.
Record revision/build, browser or desktop-shell (e.g. Electron) mode, window size, scenario/state and scoped artifact
paths. Use disposable data, bound captures and exclude credentials/unrelated user content.

## Make the review actionable

For each finding record the observed versus expected behaviour, user impact, source/evidence,
confidence and disposition. Fix and reverify actionable in-scope defects; record unrelated useful
findings in existing or deduplicated project issues. Treat aesthetic preferences as proposals for owner
review, not objective failures. Avoid speculative redesigns and unrelated component replacement.

Stop collecting when selected acceptance questions are answered. Expand only when a finding needs
another targeted check or the agreed task requires it. This skill does not lower existing required
gates, approve a baseline change, authorize installations/configuration changes or schedule recurring
audits. Missing optional tools do not create new mandatory infrastructure; use supported existing
tools and disclose limits. Missing evidence required by the task remains an acceptance gap.

## Use across projects and coding interfaces

Keep this directory together: `SKILL.md` routes to the three relative `references/` files.
`agents/openai.yaml` is optional Codex display metadata; the instructions do not depend on it.
Install the directory under the coding interface's supported skills location, or link it from a
version-controlled checkout that will remain available. A link alone does not make an interface
discover skills; use that interface's documented discovery or instruction mechanism. Keep project
commands, acceptance gates and issue-tracker conventions in the project's own guidance.
