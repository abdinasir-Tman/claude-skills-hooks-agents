---
name: repo-security-review
description: Security review of the pending changes in any repository using that repo's threat model (.claude/review/security-rules.md, built by review-rules) plus stack checklists for Express/Hono, Prisma, Mongoose, raw SQL, Go, React/Vite, Next.js, Firebase, Expo, Better Auth, Socket.io, payments/webhooks and uploads. Runs the read-only security-reviewer agent. Use in the github-issues verification gate when a change touches auth, permissions, routes or other input, database queries, payments, uploads, secrets/config or dependencies; or when the user asks for a security review of their branch/diff in a repo. Prefer it over the generic built-in security-review.
---

# Repo security review

The method lives in `${CLAUDE_PLUGIN_ROOT}/agents/security-reviewer.md`. The repo's threat model lives in `<repo>/.claude/review/security-rules.md`. This skill checks the inputs, starts the agent and relays its report.

## When to run

Run when the diff touches: auth or permissions, API routes / server actions / functions / socket events or any other input, database queries or schema, payments or webhooks, uploads, secrets or config (CORS, cookies, env), or dependencies. Skip only for pure styling, copy or docs — and say so with the reason.

## 1. Inputs

- **Repo root:** `git rev-parse --show-toplevel`.
- **Range:** the caller's range if given (github-issues gate: `<commit before the work>..HEAD`; wave: `<pre-wave commit>..plan/<name>`). Otherwise let the agent resolve a base that shares history.
- **Issue number(s)** for context, if any.

## 2. Make sure the rules exist

Same as gap-review: `security-rules.md` missing → run `review-rules` first; if the user can't be asked now, continue (the agent marks `RULES: MISSING` and derives a minimal threat model) and tell the user to run `/review-rules`.

## 3. Run the reviewer — never inline

Start `Agent` with `subagent_type: "review-system:security-reviewer"`. Prompt:

```
Repo root: <path>
Range: <base>..HEAD | "resolve it yourself"
Issues: <Keyd-Solutions/<repo>#<n>… | none>
Return at most ~15 lines plus one line per finding.
```

If the agent type isn't available in this session, use `subagent_type: "general-purpose"`, `model: "opus"`, `effort: "high"`, with the full body of `${CLAUDE_PLUGIN_ROOT}/agents/security-reviewer.md` (after the front matter) above the inputs, adding: "Only use Read, Glob, Grep and read-only Bash; never edit."

## 4. Relay and follow up

- Relay faithfully; no softening, no unverified additions.
- **FIX_BEFORE_MERGE** → fixes applied, then review again.
- A finding that is a live bug outside the current work → offer to track it per the github-issues skill.
- **Rules to refresh** → offer `/review-rules --section <name>`.
