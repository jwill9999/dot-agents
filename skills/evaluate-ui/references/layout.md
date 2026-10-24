# Layout review

Read when the selected task changes appearance, layout or responsiveness, or the owner requests a
bounded visual review. Start with the affected panel or page and its real user state.

- After the focused journey reaches its expected state, save a screenshot at a representative
  supported window size. Add a narrow/larger window or zoom case when resizing, wrapping or
  overflow is affected; do not add a device matrix for an unrelated change.
- Inspect the image, rather than merely confirming a file exists. Check hierarchy, readable
  copy, spacing/alignment, clipping, scrolling and visibility of the next relevant action.
  Include a waiting, error or empty state only when the change can affect it.
- Use the actual Electron window for desktop claims. A browser rendering can help investigate the
  shared web UI but does not establish native Electron behaviour.
- Compare with an accepted design or source-matched before image where available. Without one,
  distinguish an observable defect from a subjective improvement suggestion. Do not invent a
  pixel-perfect reference or accept new screenshot baselines without reviewing the changed image.
- Keep screenshot comparisons in a consistent platform/browser/font/scale environment. A
  cross-platform pixel difference alone does not establish a product regression. Do not mask the
  changed region or relax thresholds to make a broken layout pass.

Use the findings before finalising the layout. Reuse the inspected image before completion when
its source/build and scenario remain applicable; retake it after changes to the affected render.
Retain existing functional and backend assertions for the journey.

[Playwright visual comparisons](https://playwright.dev/docs/test-snapshots) describe environment
sensitivity and baseline handling. [Electron automation](https://playwright.dev/docs/api/class-electron)
provides actual-window screenshots; its API is experimental, so record installed-version limits.
