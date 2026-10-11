# C6.5.10 — VS Code Extension Development Host Crash
# Detailed Failure Record / Deferred Repair

## 1. Status and decision

Status: DEFERRED — NOT FIXED
Priority: Preserve evidence and complete C6.5 closeout without this test.
Owner: PacePilot development workflow
Scope: C6.5.10 real VS Code Extension Development Host test.

This record documents an unresolved failure. It does not indicate that
the Host test, real terminal execution, or end-to-end verification passed.

User decision:
- Stop spending time on this failure during the current C6.5 closeout.
- Skip the failing test and all follow-up tests whose purpose is to
  reproduce, isolate, or diagnose this same failure.
- Do not relaunch the crashing test window.
- Keep the failure recorded for a future, explicitly authorized repair.
- Continue independent C6.5 work that does not depend on this Host test.

## 2. User-observed symptoms

The user reports that:
1. The test launches a new VS Code Extension Development Host window.
2. The new window waits for approximately 10 seconds.
3. The newly opened window then closes/crashes unexpectedly.
4. The user observes exit code 3.
5. The problem remained unresolved for more than one day and blocked
   progress on C6.5.

The exact process that returned exit code 3 has not been conclusively
identified. Do not assume it was the main VS Code process, extension host,
test launcher, or terminal process without preserved process-level evidence.

## 3. Known files and test path

Known launcher:
- `run_c6_5_10_host_test.js`

Known Host test:
- `vscode-extension/c6_5_10_test_extension/host_test.js`

Related execution path under test:
- Launch a VS Code Extension Development Host.
- Activate the test extension.
- Dispatch a terminal command through the VS Code integration.
- Observe command completion and obtain the real result.
- Verify command identity, output, and exit-code reporting.

The Host test is intended to validate real VS Code behavior. Unit tests and
mock VS Code APIs cannot substitute for this real Host validation.

## 4. Previously observed error messages

The following observations have appeared during prior troubleshooting:

A. Terminal initialization / ConPTY:
`Cannot find conpty.dll at , error code: 3`

B. Command completion wait:
`waitForResult` timed out waiting for `command-1`

C. Shell Integration availability:
`Timed out waiting for Shell Integration; command was not dispatched`

These are recorded as separate observations. Current evidence does not establish
that all three have the same root cause.

The `conpty.dll` message is a lead for future investigation, not proof that
ConPTY is the sole cause of the window crash.

The `command-1` timeout is evidence that the expected result was not received
within the test's wait period. It does not, by itself, prove whether the
command was dispatched, whether the extension activated, or whether the
completion event was lost.

A previous run also produced an exit-code file containing `1`. Do not conflate
that observation with the user's reported exit code `3`; preserve the exact
log and process association if this issue is reopened.

## 5. What is and is not established

Established:
- The user repeatedly observed the new Host window close after roughly
  10 seconds.
- The user reports exit code 3.
- The problem remained unresolved through extended troubleshooting.
- A prior command-result wait timed out for `command-1`.
- A ConPTY-related error message was observed.
- The real Host execution path has not been verified as passing.

Not established:
- Which process emitted exit code 3.
- Whether the ConPTY message directly caused the crash.
- Whether the command was dispatched in the failing run.
- Whether the failure is caused by environment configuration, VS Code,
  extension activation, terminal initialization, event timing, or a
  combination of factors.
- Whether the issue can be reproduced in a clean environment.

Do not invent a root cause or mark the failure fixed without evidence.

## 6. C6.5 closeout policy

Until explicitly reopened by the user:
- Do not execute `run_c6_5_10_host_test.js`.
- Do not execute `vscode-extension/c6_5_10_test_extension/host_test.js`
  through another launcher or equivalent invocation.
- Do not run diagnostic tests whose purpose is to reproduce or isolate this
  same crashing Host failure.
- Do not automatically retry the test after unrelated changes.
- Do not block independent C6.5 closeout work on this failure.
- Do not delete the test files or erase historical evidence.
- Do not describe the real Host execution path as PASS.
- Report C6.5.10 Host validation as DEFERRED / SKIPPED, NOT PASS.

Independent unit tests, syntax checks, Python regressions, compile checks,
and diff checks may still run if they do not launch or diagnose the failing Host.

## 7. Future repair plan — only when explicitly reopened

Step 1 — Preserve evidence
- Copy existing logs, exit-code files, launcher output, and timestamps to a
  dedicated diagnostic folder before another attempt.
- Record the exact command used, working directory, VS Code executable path,
  process IDs, and exit code for each process.
- Never overwrite the only copy of a previous failure log.

Step 2 — Identify the failing process
- Distinguish the launcher process, VS Code main process, Extension Host,
  terminal process, and any child process.
- Attribute exit code 3 to a specific process using captured evidence.
- Keep unrelated exit-code observations separate.

Step 3 — Investigate startup and ConPTY evidence
- Verify the installed VS Code version and executable path.
- Inspect the original ConPTY error context and how the expected DLL path
  was resolved.
- Determine whether the DLL was absent, its path was empty, or initialization
  failed for another reason.
- Do not change system files or reinstall components without evidence.

Step 4 — Investigate extension activation and command dispatch
- Preserve extension activation logs.
- Verify whether the test extension activates before the wait timeout.
- Determine whether Shell Integration becomes available.
- Distinguish command-not-dispatched from command-dispatched-but-result-missing.
- Trace `command-1` from request through execution identity to final result.

Step 5 — Controlled validation
- Run a Host test only after the user explicitly authorizes reopening the issue.
- Use one controlled attempt with process-level logging.
- Verify actual dispatch, output capture, exit-code capture, and final status.
- Do not infer success from a window remaining open or a request returning HTTP 200.

Step 6 — Exit deferred status
Only remove the deferred status after:
- The root cause or a demonstrably effective correction is documented.
- The real Host test completes without the observed crash.
- The real command result and exit code are captured and verified.
- Relevant regression checks pass.
- Evidence is retained for later audit.

## 8. Current verification evidence — separate from Host validation

Prior recorded checks:
- `node --check vscode-extension/terminal_control.js`: PASS.
- `node tests/test_vscode_terminal_control_c4_5_6.js`: PASS.
- Focused Python terminal regression: 31 tests, OK.
- `python -m compileall -q application`: PASS.
- `git diff --check`: PASS, with LF/CRLF conversion warnings.

These checks cover independent code paths and do not establish that the real
VS Code Extension Development Host test passes.

## 9. Integrity and change history

This record is a deferred-failure report, not a fix.
Do not rewrite historical observations as verified root causes.
Do not silently convert DEFERRED / SKIPPED into PASS.
Do not commit or push this file unless the user explicitly authorizes it.
