---
name: critique-plan
description: "Independently reviews an implementation plan against requirements, source code, tests, dependencies and feasibility, without editing the reviewed work. Use when the user asks to review, critique, sanity-check or challenge a plan, spec or design before implementation. Fallback: prefer a project-specific critique skill when one exists."
---

# Critique plan

Use the project's instructions and actual review assignment. Inspect a plan independently from its
author, with relevant requirements, source/tests, task/dependency records, proposed verification,
delivery mapping and unresolved questions. Do not rely solely on the author's summary.
Prefer the project's applicable critique skill; do not duplicate the same review under both names.

Keep the assignment read-only: do not edit reviewed material, mutate task/Git/external state or
dispose your own findings. Use tools actually permitted by the session. A read-only assignment does
not establish technical tool isolation. Do not spawn other agents unless authorized. If this is a
self-review or independent review cannot be obtained, label that limitation rather than inventing
an independent approval.

Check:

- Objective, bounded scope/non-goals, testable requirements and a clear MVP stopping point.
- Current-code evidence, unsupported assumptions, affected interfaces and shared execution boundaries.
- Task identity/order, real dependencies, responsibilities and final integration ownership.
- Feasible environment/data/reset, credentials and cost assumptions; no secret inspection needed.
- Meaningful relevant tests, independent effects, negative cases and disclosed fixture boundaries.
- Agreement among the plan, task tracker and definition of done; preserved unrelated work.
- Delivery/review/owner authority and unresolved material choices, without inventing approval gates.

Scale findings to concrete risk. Do not demand unrelated infrastructure, a universal test matrix or
another project's tooling merely to make a bounded plan appear comprehensive. Missing required
evidence is a gap; planned coverage is not a passed test.

Return a verdict and actionable findings with stable ID, severity, requirement/source reference,
consequence and a feasible correction or decision. Use `approved` only when no actionable findings
remain; `correction_required` for repairable gaps, `rejected` for unsafe/infeasible proposals and
`human_decision_required` for an unresolved owner choice. Recheck affected semantics after fixes and
preserve the original findings/dispositions and reviewed revision. Approval here is a review verdict,
not owner acceptance, implementation permission or merge/release authority.
