# Frontend investigation

Read for a reproduced UI responsiveness/rendering/network symptom or a task with a frontend
performance acceptance criterion. Routine backend work does not require a browser trace.

## Select the right instrument

- In Chrome, use the available Chrome DevTools MCP for relevant console errors, request timings,
  screenshots and a short trace of the affected interaction. Listing a page proves a connection,
  not that it is inspecting the intended app or build; verify the target first.
- For Electron, prefer existing Playwright Electron capture and application diagnostics. Chrome
  DevTools MCP officially supports Chrome/Chrome for Testing; a CDP endpoint does not establish
  Electron compatibility. Use direct Electron attachment only after separately verifying it in an
  authorized isolated development configuration. Do not enable global/public debug ports.
- Use API/run diagnostics for provider waits, backend retries and request processing. Browser
  timings are not server spans or evidence of host CPU/disk saturation. Record a missing signal
  honestly and select a narrow follow-up rather than inventing a cause.

## Collect, interpret and stop

Reproduce the affected interaction first. Inspect existing console/network/failure artifacts before
recording a trace. Capture only the relevant interval and requests; note build, cache state and
other known workload. Compare like-for-like source/environment when judging an improvement.

Before repair, state the observed symptom, expected behaviour and evidence for any suspected
cause. After repair, repeat the affected measurement and functional journey. One slow sample,
an unrelated failed request or a screenshot alone is not a demonstrated regression or cause.
Use an agreed threshold where the task has one; do not introduce arbitrary timing gates or
weaken existing test deadlines. Keep a real failing measurement alongside its repaired result.

Close the investigation when the scoped question is answered or report the precise evidence gap.
Do not collect traces for unrelated screens or add a monitoring stack to resolve a small UI task.
Check the tool's data-collection configuration before sensitive captures; use disposable data.
An unavailable optional MCP can be replaced by supported existing instrumentation, but not by an
invented pass where the task requires an actual measurement.

[Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp) documents supported
browsers, trace/network capabilities and optional usage-statistics/CrUX requests. Configuration
changes require their own applicable authorization; the skill does not change them automatically.
