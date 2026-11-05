---
name: review-rules
description: Learn a repository once and write its review rulebooks — `.claude/review/security-rules.md` (threat model, tenancy, auth, public-route allow-list, validation, webhooks, secrets) and `.claude/review/gap-rules.md` (repo MUST/NEVER rules, layout, registration points, conventions, the data-access stack per package with versions and its patterns) — from evidence in the code, with the user confirming anything uncertain. Used by gap-review, repo-security-review and query-review (and by the data-access skill when writing queries), which run it automatically when a repo has no rules yet. Use when the user types /review-rules, asks to "learn this repo for reviews", "set up review rules", "refresh the review rules", or when a reviewer reports the rules are stale. `--rebuild` starts over; `--section <name>` refreshes one section.
---

# Review rules

Writes the per-repo rulebooks that the global reviewers (`gap-reviewer`, `security-reviewer`, `query-reviewer`) and the `data-access` skill read. The reviewers carry the **method**; these files carry the **repo's facts**. Nothing is assumed — every rule comes from evidence in this repo or from the user.

Files:
- Stack checklists: `~/.claude/skills/review-rules/stacks/*.md` (Detect / Discovery / Gap checks / Security checks).
- Templates: `~/.claude/skills/review-rules/templates/security-rules.md`, `gap-rules.md`.
- Output: `<repo root>/.claude/review/security-rules.md` and `gap-rules.md`.

## Modes

- **Build** (no rules files, or `--rebuild`): steps 1–6.
- **Refresh** (`--section <name>`, or a reviewer reported a stale section / uncovered pattern): run steps 1–4 only for the affected section(s), show the user the proposed diff of the rules file, write it after they agree, update the `Built from` line.

## 1. Find the repo and stacks

- Repo root: `git rev-parse --show-toplevel`. Monorepos: one pair of files at the root covering all packages; sections name the package when rules differ.
- Detect stacks **per package**: read each `stacks/*.md` **Detect** line and check it (`package.json` deps per package, `go.mod`, `firebase.json`, `schema.prisma`, …). Record the installed version of every data library from the lockfile (`package-lock.json` / `pnpm-lock.yaml` / `yarn.lock`, `go.sum`, …) — the rules must match that version.
- Unknown stack with no checklist → still build the rules from steps 3–4 and tell the user a checklist for it is missing. For a data library without a checklist, also derive its eager-load, batch-by-ids, transaction, run-in-parallel and query-log APIs **for the installed version** (its types/README in the dependency folder → Context7 → official docs) and write them with ✗/✓ examples and the doc source into gap-rules.md → Data access, so writers and reviewers don't look them up again.

## 2. Existing curated knowledge

Read, if present: `CLAUDE.md` (root + nested), `CONTRIBUTING.md`, `docs/` files about rules/conventions/architecture/security, and existing reviewer agents in `.claude/agents/` (e.g. `gap-reviewer.md`, `security-reviewer.md`, `*-reviewer.md`, `*-checker.md`). Rules in those agents are curated by the user — carry them over as FACT with `source: .claude/agents/<file>:<line>`. Repo-specific instructions about issue trackers (Jira etc.) are not rules — drop them.

## 3. Gather evidence — in a fresh read-only subagent

Spawn `Agent` (`subagent_type: "Explore"`, thoroughness "very thorough") so the evidence gathering doesn't flood this session. Give it: repo root, detected stacks, the absolute paths of those stacks' checklist files (it reads their **Discovery** sections), and the files from step 2. It must:

- answer every Discovery question of every detected stack;
- list **every** route/function endpoint with method, path, file:line and its middleware/guard chain (for Firebase: every exported function and its auth check);
- open 2–3 peers per artifact kind (route, controller, service, schema, migration, page, component, hook) to derive layout, naming and registration points; grep one peer's name to find every place it is registered;
- read lint/tsconfig/test configs and the package scripts;
- return a list where each line is `FACT | GUESS | ASK` + statement + evidence (file:line). FACT = proven by code. GUESS = likely, needs confirmation. ASK = can't tell. Every unauthenticated endpoint is GUESS (looks intended: webhook, login, callback, health, public catalogue GETs) or ASK (anything else). Tenancy is a GUESS until the user confirms it.

## 4. Confirm with the user

Show only the GUESS and ASK items, grouped (tenancy, public routes, threat model, other), as short yes/no or pick-one questions — use `AskUserQuestion` for up to 4 at a time, plain text for long lists. Also propose the **threat model**: the 3–5 worst outcomes for this repo, derived from the FACTs (tenant leak, cross-user access, forged payment webhook, admin takeover, file exposure …), and ask the user to confirm or reorder.

An ASK the user answers "no, it shouldn't be public" is a live security bug: tell them plainly and offer to track it per the github-issues skill.

If the user isn't available to answer, write the files with those items marked `UNCONFIRMED` and `Confirmed by user: NOT YET`; reviewers then treat UNCONFIRMED public routes as findings, not as allowed.

## 5. Write the files

Fill both templates. Rules:
- Every rule ends with its `— source:`.
- A section with no evidence: `N/A — <what was searched>`. Never leave template placeholder text.
- `Stacks:` lists the checklist names the reviewers must load.
- `Refresh when changed:` lists the concrete files/dirs the rules depend on (schema, app entry/mount file, middleware dir, auth config, router/nav config, CLAUDE.md, lint/tsconfig).
- `Built from:` = `git rev-parse --short HEAD` and today's date.
- Keep each file under ~250 lines: rules, not essays. Stack-generic checks stay in the checklists — the rules file holds only what is specific to this repo (names, paths, lists, decisions).

## 6. Hand over

Tell the user the two paths, the counts (rules, public routes, UNCONFIRMED items), any live bugs found, and that the files should be committed to the repo (they are shared with teammates and cloud sessions). Do not commit unless the user asks. If the repo has old reviewer agents whose content is now in the rules files, list them and suggest removing them so they can't drift (removing them is a repo change — ask first).
