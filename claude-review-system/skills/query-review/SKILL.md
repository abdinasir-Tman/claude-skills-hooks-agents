---
name: query-review
description: Data-access review of pending changes, or an audit of existing code, in any repository — request waterfalls, N+1 queries, relations not used, sequential independent awaits, parents loaded only for an id, over-fetching, unbounded lists, missing indexes, frontend wasted requests (eager fetching, duplicate requests, over-polling, over-invalidation, effects that trigger requests), and compliance with the issue's Query plan / Data loading plan. Runs the read-only query-reviewer agent and lists what the gate must measure with the query log. Use in the github-issues verification gate (step 4) whenever a change touches DB queries, models or migrations, endpoints that return data, or page/screen data loading; when the user asks to check queries, waterfalls, N+1 or the performance of a change; or with --audit <path> to find existing waterfalls in a codebase.
---

# Query review

The method lives in `~/.claude/agents/query-reviewer.md`. The rules are the `data-access` skill (shapes + plan formats), the **Data access** sections of the stack checklists (`~/.claude/skills/review-rules/stacks/`), and the repo's `<repo>/.claude/review/gap-rules.md` → **Data access**. This skill collects the inputs, starts the agent, relays its report, and runs the measurement.

## When to run

The diff touches DB queries or ORM calls, a schema/model/migration, an endpoint / handler / server action / function / job that returns or writes data, or how a page or screen loads data (query hooks, loaders, server components). Skip for changes with no data access (styling, copy, docs, pure UI) — and say so.

## 1. Inputs

- **Repo root:** `git rev-parse --show-toplevel`.
- **Diff mode:** the gate's range — `<commit before the work>..HEAD`; wave: `<pre-wave commit>..plan/<name>`.
- **Audit mode** (`--audit <path>`): a folder of existing code, no diff.
- **Issue number(s)** — pass numbers, not pasted text; the reviewer reads the Query plan / Data loading plan itself.

## 2. Rules

`gap-rules.md` missing → run `review-rules` first. If the user can't be asked now (unattended run), continue — the agent marks `RULES: MISSING` — and tell the user to run `/review-rules`.

## 3. Run the reviewer — never inline

Start `Agent` with `subagent_type: "query-reviewer"`:

```
Repo root: <path>
Range: <base>..HEAD        (or: Audit path: <path>)
Issues: <Keyd-Solutions/<repo>#<n>… | none>
Return at most ~15 lines plus one line per data path and per finding.
```

If the agent type isn't available in this session (agents load at session start), use `subagent_type: "general-purpose"`, `model: "opus"`, `effort: "high"`, with the full body of `~/.claude/agents/query-reviewer.md` (after the front matter) above the inputs, adding: "Only use Read, Glob, Grep and read-only Bash; never edit."

## 4. Measure (gate step 4b)

The agent predicts; the measurement proves. For each line under **Measure in the gate**, on local or test data only (never production — check the env's DB host first):

- **Endpoints:** turn on the query log — the repo's switch from gap-rules.md → Data access, else the stack checklist, else the installed library's logging/debug/tracer option from its docs (or the database's own statement log on a local server). Call the endpoint with 1 row and with 20 rows of data and count statements per request. Both counts must equal the plan. A test with a query counter is just as good. No way to log queries in this repo → say so in the report and suggest adding a switch (a repo change, tracked per github-issues).
- **Screens:** load the page with the browser's network log (`claude-in-chrome`) and check its requests are exactly the Data loading plan's list (shell row included): they start together on navigation (and on link hover where preloading is on); nothing extra — no other screens' data, no closed dialog's data, no duplicates; nothing re-sent on window focus or tab switch unless planned; each save causes only its planned refresh.

Record **planned → measured** for the verification report. A mismatch is a finding: fix it, then review and measure again.

## 5. Relay and follow up

- Relay the report faithfully — don't soften verdicts or add unverified findings.
- **NEEDS_FIXES** → fixes applied → review again (a fix can add a new waterfall).
- **PLAN MISSING** → the issue's Query plan / Data loading plan is written first (github-issues §3), then the code is checked against it.
- **Audit mode:** present the findings grouped by endpoint/screen and offer to open issues for them per the github-issues skill. Don't fix unasked.
- **Checklist missing: <library>** → the review still ran on the universal rules; tell the user, and the next `/review-rules` records that library's patterns in the repo's gap-rules.md (or offer to add a global checklist for it).
