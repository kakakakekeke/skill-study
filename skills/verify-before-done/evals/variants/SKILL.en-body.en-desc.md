---
name: verify-before-done
description: Carries out a change to application code in a repo with tests, a type checker, or a linter and finishes it with a fresh run of tests, type check, and lint and a read of the exit code, via a deterministic preflight script (changed-file test selection, ruff/mypy, short JSON). Use for any such change (a flag, a rename, a refactor), and when the user asks if a change is ready, what else broke, or to make sure CI passes. Not for writing new tests, configuring linters or CI, summarizing a failing log, measuring a flaky test, or explaining tests.
---

# verify-before-done

"The tests should pass" is not verification. Guessing the result in your head after the last edit is how false completions happen: a call site in another module breaks, the tests pass but the type check fails, or an import error means zero tests ran and "no failures" gets read as "passed". CI failure is the number-one reason agent PRs get rejected. This skill has one rule: **run fresh after the last edit, read the exit code, and only then say it is done.**

## Procedure

1. Finish the code change. Any run made in the middle of editing is void once you edit again.
2. Run. The script is `scripts/preflight.py` in this skill's directory.
   ```bash
   python3 <skill-dir>/scripts/preflight.py            # git diff → tests related to changed files + ruff + mypy
   python3 <skill-dir>/scripts/preflight.py --all      # full suite if you don't trust the selection
   ```
   Without git, or when the changed files are not .py, it falls back to the full suite. Output is a few dozen lines of JSON plus a final `[preflight] verdict=… exit=…` line. If ruff or mypy is not installed it is reported as `skipped` (which is not a pass).
3. Read the exit code.
   - `0` PASS: at least one test passed, lint and types clean.
   - `1` FAIL: failing tests or lint/type errors. Start from `first_failures` / `first`, fix, go back to step 1.
   - `2` ZERO_TESTS_RAN: no test executed (collection error, import failure, empty selection). This is not a pass but a **failed run**. Fix the ImportError in `tail` first.
4. Only then report completion. Quote the last run verbatim in the final message:
   ```
   Verified: python3 …/preflight.py → exit 0 (pytest 8 passed, ruff 0, mypy 0)
   ```
   If you have to stop in a failing state, write the exit code and the remaining failures as they are. That beats hiding what you could not fix.

## If you did not run it, say so

Do not write estimates such as "should pass", "probably works", "tests should be green now". If there is a reason you could not run (missing dependency, external service), write "not run" and the reason. Writing a guess as if it were a confirmation is exactly the failure this skill exists to prevent.

## Stacks preflight does not cover

For JS/TS and other non-Python stacks, run the native runner directly and apply the same rule. Trim output with `| tail -30` and read the exit code with `; echo "exit=$?"`.

```bash
npx vitest run 2>&1 | tail -30; echo "exit=${PIPESTATUS[0]}"
npx tsc --noEmit 2>&1 | tail -20; echo "exit=${PIPESTATUS[0]}"
```
