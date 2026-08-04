---
description: Write, run, and fix pytest coverage for a Spendly feature, then report it against the spec's Definition of Done
argument-hint: "Feature name or step number, e.g. 3 or 'login and logout'"
allowed-tools: Read, Glob, Agent
---

You are coordinating end-to-end test verification for a Spendly feature, using its spec in `.claude/specs/` as the
source of truth. Always follow the rules in CLAUDE.md.

User input: $ARGUMENTS

## Step 1 - Resolve the spec

From $ARGUMENTS, find the matching spec file in `.claude/specs/<nn>-<slug>.md`:
- If given a step number, match the `<nn>` prefix.
- If given a feature name, match it against the spec titles/slugs (fuzzy match on words is fine, e.g. "login" matches
  `03-login-and-logout.md`).
- If nothing matches, or more than one spec matches ambiguously, list the candidates and ask the user to pick one
  rather than guessing.

Read the matched spec file in full, and note its `feature_slug` (the `<slug>` part of the filename) and its
**Definition of Done** checklist.

## Step 2 - Write or refresh the tests

Invoke the `spec-test-writer` agent for this spec, so it (re)generates `tests/test_<feature_slug>.py` from the
spec's Definition of Done, Routes, and Database Changes sections. Pass it the spec file path directly so it doesn't
have to re-resolve $ARGUMENTS itself.

## Step 3 - Run and fix

Invoke the `test-runner` agent, scoped to `tests/test_<feature_slug>.py` (not the whole suite, unless the spec-test-
writer step touched shared fixtures in `tests/conftest.py`, in which case ask it to run the full suite to check for
regressions). Let it diagnose and fix failures per its normal rules — including leaving alone any check that fails
only because the feature it covers is intentionally unimplemented per CLAUDE.md.

## Step 4 - Report

Print, in this order:
1. Spec file used and feature title
2. Final pytest result for `tests/test_<feature_slug>.py` (and full suite, if run)
3. The spec's Definition of Done checklist, each item marked done/not-done based on what the tests actually verify
   — not assumed
4. Anything left not-done because it's an intentionally unimplemented step, or a spec/implementation mismatch
   surfaced by either subagent

Do not silently mark a Definition of Done item as done if no test actually exercises it — call that out as
untested rather than guessing.
