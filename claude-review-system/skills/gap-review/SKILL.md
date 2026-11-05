---
name: gap-review
description: Audit implemented work against its GitHub issue(s), plan or task description in any repository, using the repo's own rulebook (.claude/review/gap-rules.md, built by review-rules) plus the stack checklists. Runs the read-only gap-reviewer agent so the implementer never certifies itself; finds missed, partial, skipped or silently changed work and violations of the repo's rules. Use after implementing an issue, a wave or a plan, in the github-issues verification gate, or when the user asks "is this fully implemented", "check for gaps", or "did anything get skipped".
---

# Gap review

The method lives in the global agent `~/.claude/agents/gap-reviewer.md`. The repo's facts live in `<repo>/.claude/review/gap-rules.md`. This skill checks the inputs, starts the agent, and relays its report.

## 1. Collect the inputs

- **Repo root:** `git rev-parse --show-toplevel`.
- **Spec:** GitHub issue number(s) + repo (`Keyd-Solutions/<repo>`) — pass the **numbers**, never a pasted body, so the reviewer reads the latest body, comments, scope updates and sub-issues itself. Or a plan file path, or the user's task description (verbatim) when there is no issue.
- **Base:** the commit before the work (github-issues gate: the commit the issue branch started from, or the pre-wave commit). If unknown: `git merge-base HEAD <base branch from the github-issues repo table>`. Never assume `main`.
- **Optional:** the implementer's report and the coverage table from an orchestrated wave.

## 2. Make sure the rules exist

- `<repo>/.claude/review/gap-rules.md` missing → run the `review-rules` skill first (it asks the user to confirm doubtful items). If the user can't be asked now (e.g. inside an unattended run), continue — the reviewer falls back to quick inference and marks `RULES: MISSING` — and tell the user afterwards that `/review-rules` should be run.
- File exists but says `Confirmed by user: NOT YET` → continue, and mention it in the result.

## 3. Run the reviewer — never inline

Start `Agent` with `subagent_type: "gap-reviewer"`. Prompt:

```
Repo root: <path>
Spec: <Keyd-Solutions/<repo>#<n>[, #<m>…] | plan file <path> | task: "<verbatim>">
Range: <base>..HEAD   (or: working tree vs <base>)
Implementer report: <short report or "none">
Coverage table: <table or "none">
Return at most ~15 lines plus one line per spec item.
```

If the `gap-reviewer` agent type isn't available (agents load at session start — a session started before the file existed won't see it), use `subagent_type: "general-purpose"`, `model: "opus"`, `effort: "high"`, and put the full body of `~/.claude/agents/gap-reviewer.md` (after the front matter) above the inputs, adding: "Only use Read, Glob, Grep and read-only Bash; never edit."

Run it on the branch under review in the main checkout (no worktree) unless the caller says otherwise.

## 4. Relay and follow up

- Relay the report faithfully — don't soften verdicts or add findings the agent didn't verify.
- **NEEDS_FIXES** → the fixes are applied (by whoever owns the work), then run the review again: a fix round can introduce or reveal gaps.
- **Rules to refresh** listed → offer `/review-rules --section <name>` (or run it if the user already asked for rule upkeep).
- `RULES: MISSING` → tell the user to run `/review-rules` in this repo.
