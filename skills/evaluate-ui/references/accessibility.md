# Accessibility at the appropriate scope

Basic usability of changed controls belongs in the local MVP. An application-wide accessibility
audit, broad screen-reader matrix or compliance certification is a separate agreed evaluation.

## During ordinary UI work

After implementing a changed interactive surface, use the actual browser/Electron journey to check
the relevant behaviour before completion:

- Controls have meaningful accessible names and appropriate roles; keyboard users can reach and
  activate them, see focus and leave the interaction without a keyboard trap.
- Changed dialogs manage initial focus and return focus appropriately. Changed status/error content
  remains understandable without colour alone; evaluate announcements when their delivery changes.
- If typography, colours, size or layout changed, inspect readable text, applicable contrast and
  focus visibility, and relevant zoom/reflow. Select the affected checks, not every item by default.
- Use existing accessible Playwright locators/assertions. If an approved accessibility scanner is
  already available, run it on the changed state; do not install one as a hidden prerequisite.

For API-only work, select a focused accessibility check only if the change alters a visible
interaction or its semantics. No changed surface means no new accessibility audit.

## When to broaden

Use a wider, explicitly bounded accessibility review when requested, during a navigation/design
system change affecting many consumers, or when observed repeated defects justify it. Set its
target surfaces, assistive technologies and acceptance criteria in the task. A release accessibility
assessment is separate from a routine local-MVP fix.

## How to use the data

Fix and retest an in-scope obstacle to using the changed control. Review scanner results against the
real DOM/state; retain items needing manual assessment. Record unrelated existing findings for
backlog review rather than silently expanding the task. Recheck affected evidence after a fix.
An automated pass or screenshot is not proof of complete accessibility or a compliance claim.

[Playwright accessibility testing](https://playwright.dev/docs/accessibility-testing) explains
automated checking and why it needs manual evaluation alongside it.
