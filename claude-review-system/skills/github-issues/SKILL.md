---
name: github-issues
description: Track all work in GitHub Issues (org Keyd-Solutions) — repo work and non-repo work alike; Jira is retired since 2026-10-26. Plans as Feature parent issues with sub-issues, blocked-by links, an org Project board with To Do → Analysis → In Dev → In Review → Done, PRD and spec templates, the verification gate, and parallel worktree implementation. Use before starting any code change, bug fix, feature, migration or multi-step plan in any repo, before non-repo work (skills, tooling, home folder → Keydsolutions-tools), when the user asks for status, "what's left", "continue the plan", approves or rejects work in review, asks to implement or orchestrate a plan's issues, or types /github-issues.
---

# GitHub Issues work tracking

All work lives in GitHub Issues: repo work next to its code, non-repo work (Claude Code skills and tooling, the home folder, things with no repo) in `Keydsolutions-tools`. **Jira is retired (user, 2026-10-26): never create, search, update or transition Jira tickets and never use the `jira` skill or the Atlassian Jira tools**, even when old notes, memory or commits mention `AS-…` keys — those are history. Open tickets still in Jira move to GitHub only when the user asks (`reference.md`, Moving a repo's tickets from Jira).

## Constants

- Org: `Keyd-Solutions`. Assignee: `abdinasir-Tman`. **Never use a `claude-code` label (or any AI/Claude label) on issues, PRs or anywhere else** (user, 2026-10-15).
- Tool: the `gh` CLI, **2.102 or newer** (types, sub-issues and blocked-by since 2.94; board fields by name since 2.97). Every tracking action is a plain `gh` command — see **Commands** below. Check with `gh --version`; if it is older, ask the user to run `brew upgrade gh`.
- Org issue types: **Feature** (plans and sub-features), **Task**, **Bug**. Org issue field **Priority**: Urgent / High / Medium / Low (default Medium; High/Urgent only for production breakage or when the user says so).
- Labels: `blocked` (waiting on something outside GitHub), `from-jira` (moved from Jira), `user-task` (only the user can do it — accounts, business verification; agents never take it, Claude only helps with steps).
- Project board: org Project **Keyd Work** (https://github.com/orgs/Keyd-Solutions/projects/5) with Status **To Do / Analysis / In Dev / In Review / Done** and views All work, Board, Waiting for review, Nexafon, Roadmap. Project number **5**, owner `Keyd-Solutions`. Built-in workflows set Done when an issue closes or a PR merges.

## Commands

`<repo>` = the GitHub repo from §1; `<url>` = `https://github.com/Keyd-Solutions/<repo>/issues/<n>`, always written out literally (the In Review hook reads it).

Create (types: Feature, Task, Bug), then set its Status and Priority right away — a new board item has neither:
```
gh issue create -R Keyd-Solutions/<repo> --title "<title>" --body-file <file> --type Task --assignee @me --project "Keyd Work" [--parent <plan n>] [--blocked-by <n>]
```
Set Status (To Do / Analysis / In Dev / In Review / Done) and read it:
```
gh project item-edit 5 --owner Keyd-Solutions --url <url> --field Status --value "<status>"
gh issue view <n> -R Keyd-Solutions/<repo> --json projectItems --jq '.projectItems[] | select(.title=="Keyd Work") | .status.name'
```
Set Priority — an org issue field, which `gh` has no flag for. Options: Urgent `IFSSO_kgDOA-V1YA`, High `IFSSO_kgDOA-V1YQ`, Medium `IFSSO_kgDOA-V1Yg`, Low `IFSSO_kgDOA-V1Yw`. Every new issue gets one (Medium unless §Constants says otherwise). Read it with the second command:
```
gh api graphql -f query='mutation($i:ID!,$o:ID!){setIssueFieldValue(input:{issueId:$i,issueFields:[{fieldId:"IFSS_kgDOAjoHlg",singleSelectOptionId:$o}]}){clientMutationId}}' -F i="$(gh issue view <n> -R Keyd-Solutions/<repo> --json id -q .id)" -F o=IFSSO_kgDOA-V1Yg
gh api graphql -f query='query($i:ID!){node(id:$i){... on Issue{issueFieldValues(first:10){nodes{... on IssueFieldSingleSelectValue{name field{... on IssueFieldSingleSelect{name}}}}}}}}' -F i="$(gh issue view <n> -R Keyd-Solutions/<repo> --json id -q .id)" --jq '.data.node.issueFieldValues.nodes'
```
Edit the body / tick boxes (download, change `- [ ]` to `- [x]`, upload):
```
gh issue view <n> -R Keyd-Solutions/<repo> --json body -q .body > <file>
gh issue edit <n> -R Keyd-Solutions/<repo> --body-file <file>
```
Parent, sub-issues, blocked-by:
```
gh issue edit <child> -R Keyd-Solutions/<repo> --parent <plan n>        # or --remove-parent; on the parent: --add-sub-issue <n>
gh issue edit <B> -R Keyd-Solutions/<repo> --add-blocked-by <A>         # or --remove-blocked-by <A>
```
Show one issue:
```
gh issue view <n> -R Keyd-Solutions/<repo> --json number,title,state,issueType,parent,blockedBy,blocking,subIssuesSummary,projectItems
```
Board by status (add `and .content.repository=="Keyd-Solutions/<repo>"` inside `select` for one repo):
```
gh project item-list 5 --owner Keyd-Solutions --limit 500 --format json --jq '.items[] | select(.status=="In Review") | "\(.content.repository)#\(.content.number) \(.title)"'
```
Plan tree (status and open blockers of every child):
```
gh issue list -R Keyd-Solutions/<repo> --state all --limit 500 --json number,title,state,parent,blockedBy,projectItems --jq '[.[] | select(.parent.number==<plan>)] | sort_by(.number)[] | "#\(.number) \([.projectItems[] | select(.title=="Keyd Work") | .status.name][0] // "-") \(.title) | open blockers: \([.blockedBy.nodes[]? | select(.state=="OPEN") | .number])"'
```
Waves — which To Do children can start. The `!= "In Review"` test counts In Review blockers as satisfied (orchestrated run, §7); drop it otherwise:
```
gh issue list -R Keyd-Solutions/<repo> --state all --limit 500 --json number,title,state,parent,blockedBy,projectItems --jq '[.[] | select(.parent.number==<plan>)] as $c | ($c | map({key:(.number|tostring), value:([.projectItems[]|select(.title=="Keyd Work")|.status.name][0])}) | from_entries) as $st | $c[] | select(.state=="OPEN" and ($st[.number|tostring] == "To Do")) | [.blockedBy.nodes[]? | select(.state=="OPEN") | select(($st[.number|tostring] // "") != "In Review") | .number] as $open | "#\(.number) \(if ($open|length)==0 then "CAN START" else "waits for \($open)" end) — \(.title)"'
```
Close, only after the user approves (§4 Closing), then set Status Done:
```
gh issue close <n> -R Keyd-Solutions/<repo> --comment "<closing summary>"
```

**In Dev hook.** `~/.claude/hooks/github-in-dev-ready.py` (PreToolUse, next to the In Review hook) refuses any Status change to In Dev while the issue body still says `_To be filled after analysis_` or has an empty `### Query plan` / `### Data loading plan` section — Analysis ends with a complete spec. Put the issue URL literally in the command, as for In Review.

**In Review hook.** `~/.claude/hooks/github-in-review-checklist.py` (a Claude Code PreToolUse hook in `~/.claude/settings.json`) refuses any Status change to In Review while the issue body has unticked boxes, unless the command states how many are left open on purpose: `… --value "In Review"  # open-boxes: 2` (several issues: `# open-boxes: 190=2 185=0`). The count must equal the real number of `- [ ]` lines.

## 1. Repos

| Folder(s) under `~/` | GitHub repo | Tracking | Base branch |
|---|---|---|---|
| `nexafon` | `nexafon` | **GitHub** (moved 2026-10-15) | `main` (v1 and the channels plan are merged into `main`, #347, 2026-11-02). A plan integrates on `plan/<name>` from `main` and reaches `main` through a reviewed PR |
| `pms`, `pms-support-hub` | `pms` | **GitHub** (since 2026-10-26) | `feat/bulk-import` (`prod` is deploy-only) |
| `new-resto`, `resto-support-hub` | `new-resto` | **GitHub** (since 2026-10-26) | `prod` as start point only — never merge or push to it; merge target `feature-route-gates` |
| `resto-` | `Resto` | **GitHub** (since 2026-10-26) | default `staging` |
| `medly`, `medly-support-hub` | `medly` | **GitHub** (since 2026-10-26) | `prod` start point only; merge target: ask |
| `influencer-ecommerce-`, `tocktify-support-hub` | `influencer-ecommerce-` | **GitHub** (since 2026-10-26; earlier work carries `AS-…` Jira keys, history only) | `xperiment-snapshot` |
| `support-hub` | `Keydsolutions-tools` | **GitHub** (since 2026-10-26) | `main` |
| `~/.claude/skills`, the home folder, work with no repo | `Keydsolutions-tools` | **GitHub** (since 2026-10-26) | none — not repo code |

Every row tracks on GitHub. A folder not in the table: ask the user which repo, then add its row. Open tickets still in Jira are moved only when the user asks (see `reference.md`); until then never touch Jira for them.

**Base branch** = where ticket branches start and merge back (only when the user asks). Never assume `main`. Merges into a branch that is not the repo's default branch do **not** auto-close issues (`Closes #12` only fires on the default branch) — Claude closes issues itself (§4 Closing).

## 2. Size the job

| Size | Structure |
|---|---|
| Single job — one outcome, one sitting | One **Task** (or **Bug**) issue. Steps go in the work plan checklist; add sub-issues only for 3+ separately verifiable steps. |
| Big plan — several deliverables, spans sessions, or steps depend on each other | Plan structure below. |

No issue for: pure questions/explanations, discussions or analysis the user only wants in chat, reading code to answer something, one-line trivial edits.

### Plan structure (Feature → Feature → Task)

1. **Plan issue** — type Feature, title `[Plan] <name>`, in the product's repo. Its body is the **PRD** (§3). Created first, at the start of planning; Status Analysis while the plan is worked out, In Dev while children are worked, closed when the last child is closed.
2. **Sub-features** (optional) — type Feature, children of the plan, one per area, when the plan has more than ~30 tasks or would pass GitHub's **100 sub-issues per parent** limit (nesting goes 8 levels deep).
3. **Tasks** — one per independently reviewable deliverable (a migration, an API, a screen), type Task, child of the plan or its sub-feature. Body = **spec** (§3).
4. **Sub-issues of a task** — only for 3+ separately verifiable steps; otherwise a checklist in the task.
5. **Dependencies** — native blocked-by: `gh issue edit <B> --add-blocked-by <A>` for every "B can't start until A is done". Link task ↔ task; link sub-issues only for step-level dependencies.
6. Children can live in another repo of the org (e.g. a Tocktify integration task under a Nexafon plan).
7. No plan labels are needed: the plan is the parent. The **Plan tree** command shows the whole plan with status and open blockers.
8. Create children at the end of the plan's Analysis, Status To Do, blockers first, then show the user the plan tree.

## 3. Issue content

**Title:** `<Area>: <verb> <outcome>` — e.g. `Checkout: apply discount codes to online orders`. Under ~80 characters. Plans: `[Plan] <name>`.

Write bodies to a temp file in the scratchpad and pass `--body-file`. Reference other issues as `#12` (same repo) or `repo#12`. Never put secrets, passwords, tokens, connection strings or customer personal data in issues or comments.

### PRD — the plan issue

```
## Problem & goal          who has the problem, what changes for them, why now
## Users & main flows      who uses it; the main end-to-end flow step by step (the final E2E test replays it)
## Requirements            R1, R2, … each one testable; tasks cite these numbers
## Out of scope
## Success measures        how we know it worked (targets, flows passing, availability)
## Decisions               date — decision — why
## Delivery order          waves / dependency order; optional mermaid graph
## Risks & open questions
## Verification of the whole plan
```
The sub-issue panel lists the children; don't maintain a key list by hand.

### Spec — a task issue

```
## Goal
## Covers                  R-numbers from the plan
## Context                 repo/folder, background, decisions that apply, related issues
## Scope                   **In:** … **Out:** …
## Files to touch          real paths, each marked [NEW] / [MOD] / [DEL]
## Mirror                  existing file + function/type to copy the shape from (path:symbol) — its structure and conventions, never a waterfall or N+1 it contains
## Reuse                   existing functions / components / queries to call instead of rewriting (path:symbol)
## Design
### Data model / migration
### API contract           METHOD /path → request, response, errors, who may call it
### UI                     screens + loading / empty / error states; i18n keys
### Query plan             backend, one row per endpoint / function, in the repo's own ORM/SQL syntax (formats: data-access skill):
                           | Endpoint / function | Returns | Query shape (model · filter · eager-load/select · order · limit) | Sequential DB calls | Statements | Indexes |
                           related data via relations, not follow-up queries; Sequential DB calls > 1 only with a why; Statements the same for 1 and 20 rows
### Data loading plan      frontend, one row per screen + one row for the shell (formats: data-access skill):
                           | Screen / route | Loader starts (together) | Inputs | On user action | Not loaded here | Waits for (why) | Refresh |
                           + Saves: | Save | Cache update | Invalidates (exact keys) |
                           the complete request list — any other request on the screen is a finding; Waits for only with a why
### Docs checked           | library / platform | version | doc link | what we rely on |
## Work plan               - [ ] …
## Acceptance criteria     - [ ] observable, checkable outcomes
## How to verify           automated checks + end-to-end steps (local / test data only)
## Open questions          only if any
```
A section that doesn't apply gets one line `Not applicable — <reason>`; **Query plan** and **Data loading plan** are required whenever the issue adds or changes a DB query, a model/relation/migration, an endpoint that returns data, or how a screen loads data — written at the end of Analysis, before any code, in the formats of the `data-access` skill and the syntax of the repo's own stack (detected per repo: gap-rules.md → Data access, else the stack checklists' Detect lines — never assumed); otherwise `Not applicable — no data access`. Docs checked is filled when the issue uses a library/platform API. **Files to touch** and **Mirror** are what keep implementers from exploring the codebase: name the closest existing feature and the exact files, so the implementer reads those instead of searching. **Reuse** lists what it must call rather than write again (Mirror copies a shape; Reuse calls the code itself). At creation, fill Goal, Context and Scope with what is known and write `_To be filled after analysis_` under the rest; complete them at the end of Analysis. Bugs use: Summary, Steps to reproduce, Expected vs actual, Evidence (error text, logs), Cause (after analysis), Fix plan, Acceptance criteria, How to verify.

### Quality rules every spec and every change follows

- **Version first, then docs.** Read the installed version (`package.json`/lockfile, `go.mod`, Gradle, Podfile) and use docs for *that* version. Sources in order: the library's own types/README in `node_modules` or module cache → Context7 (when signed in) → the official docs (WebFetch) → real examples via `gh search code` (hints only; they must match the docs). Record what was used under **Docs checked**. If an API or option can't be found in the docs or types, say so — never guess. Typecheck and running the code are the final proof.
- **"Latest"** = the current idioms of the installed version. A major upgrade is its own issue.
- **Use the relations — no waterfalls, no N+1** (`data-access` skill; ✗/✓ code per stack in the **Data access** sections of `~/.claude/skills/review-rules/stacks/`), in whatever stack the repo uses — detect it, never assume one. Read the schema before writing a query. Related data comes in the same query through the repo's eager-load API (e.g. Prisma `include`/`select`, Mongoose `populate`, SQL `JOIN`/`json_agg`); never load a parent only to read an id you already have; independent queries run together (e.g. `Promise.all`, `$transaction([...])`, `pgx.Batch`, `errgroup`); no query inside a loop (batch by ids, bulk writes, nested writes); the tenant/owner check goes in the same filter, not a separate read. Paginate lists, select only needed columns, index FK and filter/sort columns.
- **Frontend: the route is the page's data list — no waterfalls, no wasted requests** (`data-access` skill → Frontend structure; ✗/✓ code in the stack checklists). Every page declares all its requests in its route loader (or the stack's equivalent — the repo's route to copy is in gap-rules.md → Data access) and starts them together from what is known at navigation; components read from the cache and fetch only on a user action (open, expand, click, debounced typing); nothing for closed dialogs, hidden tabs or other pages; the shell loads only small data every page shows; one query definition per resource; saves update the cache from their response and invalidate exact keys only; a realtime event updates the cache or invalidates, never both; `useEffect` never fetches or refetches. A child never waits for its parent's data to get an id the route already has; data always shown together comes from one endpoint that returns the related names itself. Server components: parallel fetches + `Suspense`, never sequential `await`s.
- **Reuse is not chaining.** Calling existing single-record helpers one after another (`getUser()` then `getPosts()`) is a waterfall, not reuse: give the helper an eager-load option or add one purpose-built query in the same service.
- **Reuse before building (DRY).** Search for an existing function, component, hook or query before writing one; call it, never copy it and change it slightly — a variation is a parameter on the existing one. Logic used in two or more places lives once, in the module that owns the concept (no new `utils`/`common` dumping grounds). No abstraction for a single caller: extract when the second caller appears. The repo's CLAUDE.md names its shared places.
- **Clean code:** follow neighbouring code and the repo's CLAUDE.md; no `any`, no TODO/stubs, no swallowed errors.

## 4. Status workflow

Status lives on the Project board; the issue itself is only open or closed.

Set Status, Board by status and Close are in **Commands**. Moving to In Review passes the In Review hook only when the checklist is up to date (gate step 6).

| Status | Move here when | Comment on the issue |
|---|---|---|
| To Do | Planned, not started | — |
| Analysis | Right after creating the issue, when starting immediately: reading code, reproducing, designing | Findings + chosen approach when analysis ends |
| In Dev | Body completed; writing code / config / migrations. Stays here through the verification gate | Progress notes on long work (optional) |
| In Review | Verification gate passed, checklist ticked; PR open with the verification report | Short comment linking the PR |
| Done | The user approves (Closing) | Closing summary: outcome, PR/commits, follow-up issues |

### Lifecycle

1. **Create first, investigate second** — the issue exists from the first minute (§3 rules for what to fill at creation).
2. Starting now → **Analysis**. To Do is only for planned-but-not-started work.
3. **End of Analysis** → complete the body (work plan, acceptance criteria, design, query plan / data loading plan, docs checked, how to verify). An issue that adds or changes data access doesn't move to In Dev without its Query plan / Data loading plan tables. **Older issues** (created before 2026-11-03) carry the old one-line Query plan / Data loading plan: when work on one that touches data access starts, write its tables first (Analysis), then move it to In Dev. For a plan, create the children and their blocked-by links. Comment the findings. Move to **In Dev**.
4. **Branch:** `gh issue develop <n> -R Keyd-Solutions/<repo> --base <base branch> --name <n>-<slug>` creates a branch linked to the issue (shows under Development). Commits: `<summary> (#<n>)` or `Refs #<n>`.
5. **Code done → verification gate.** The issue stays In Dev until it passes.
6. **Gate passed → PR + In Review.** Push the branch, open a PR into the base branch with the verification report as its description (template below; `Refs #<n>`), comment the PR link on the issue, Status → In Review.
7. **Planning only** ("plan X", "create the issues for X"): investigate, create fully detailed issues in To Do, and stop.

### Verification gate — before In Review

All six, in this order. Anything that fails is fixed while the issue stays In Dev, then the gate restarts from step 1.

**Review rules first.** Steps 2–4 read the repo's rulebooks in `<repo>/.claude/review/` (`gap-rules.md`, `security-rules.md`). If they are missing, run `review-rules` before the gate and have the user confirm its doubtful items; in an unattended run, continue (the reviewers mark `RULES: MISSING`) and tell the user to run `/review-rules`. When a reviewer lists **Rules to refresh**, offer `/review-rules --section <name>`.

1. **Automated checks** — the repo's own typecheck, lint and tests for the changed areas (scripts from `package.json` / Makefile / Taskfile / CI config; don't invent tooling).
2. **Gap review** — invoke `gap-review` with the **issue number(s)** (not a pasted body — the reviewer reads body, comments, scope updates and sub-issues itself) and the commit before the work as the base. Fix every ❌ / ⚠️, or record on the issue why it stays.
3. **Security review** — invoke `repo-security-review` (not the generic built-in `security-review`) with the same range when the change touches auth or permissions, API routes or other input, database queries, payments, uploads, secrets/config, or adds dependencies. Skip only for pure styling, copy or docs, and say so in the report.
4. **Query review + measured counts** — when the change touches data access (DB queries, models/migrations, endpoints that return data, screen data loading): (a) invoke `query-review` with the issue number(s) and the same range; fix every HIGH / MEDIUM, or record on the issue why it stays; (b) measure what its **Measure in the gate** list names, against local/test data only: statements per request from the repo's query log (or a test with a query counter), with 1 row and with 20 rows — both must equal the Query plan; screens: the network log matches the Data loading plan exactly — planned requests start together, nothing extra (no other screens' data, no closed dialog's data, no duplicates), nothing re-sent on window focus or tab switch unless planned, each save triggers only its planned refresh. (b) can be done during the step 5 run. No data access → skip and say so.
5. **End-to-end test — always last**, against **local or test data only**. Before starting, check which database and services the env points to (host names only, never print secrets); if it is production or unclear, stop, label `blocked`, comment what is needed. Some repos' `.env` points to production (e.g. `pms`).
   - start what's needed (the `run` skill covers launching)
   - API: real endpoints with curl, including bad input and missing permission
   - UI: real screens in the browser (`claude-in-chrome`): happy path, an error path, reload to prove persistence; read the network log — requests that could run together must start together, and nothing outside the Data loading plan is requested
   - backend: statements per request from the query log for each Query plan row, with 1 and 20 rows (step 4b, if a test didn't already measure it)
   - check results where they land (response, DB row, UI), re-check the nearest existing feature, stop every server you started
   - what can't be tested end to end (real payments, SMS, store review, real phones) goes under "Please check"
6. **Checklist** — tick every Work plan step that is merged and every Acceptance criterion (and How to verify check) that steps 1–5 proved, in the issue body (**Edit body / tick boxes**). A box is ticked only with evidence: a test in the repo plus a recorded passing run, a recorded end-to-end run, or the merged code for a build step. Every box left unticked is named under "Please check" with who does it (user, or Claude with the missing run). Then move to In Review, stating the open count (`# open-boxes: N`); the hook refuses a wrong count.

**PR description = the verification report** (the user reviews from it):

```
Refs #<n>

## Summary          what changed and why, 2–3 lines
## Changes          areas / files
## Verification
- Automated checks: <commands> → <result>
- Gap review: <result; open items>
- Security review: <result, or "skipped: <reason>">
- Query review: <verdict; open items, or "skipped: no data access">
- Query counts: <endpoint: planned → measured (1 row / 20 rows)>; screens: <matches the Data loading plan: together ✅/❌ · extra requests: none / list>
- End-to-end (local data): per acceptance criterion — what was done, what was seen, ✅/❌
- Checklist: <ticked> of <total> boxes ticked; open: <each open box and who does it>
## Please check
- untested parts and why; decisions to confirm; short manual test steps
```

### Closing

Claude closes an issue (**Close** in Commands: close + Status Done) only when the user approves in chat ("approved", "looks good", "close #91"), or the user asks Claude to merge/deploy it and that succeeds. Never close or move an item out of a status the user set without asking. When starting work in a repo, list issues waiting in In Review (**Board by status**) and ask whether to close them.

### Problems found in review or later

| Situation | Status | What to do |
|---|---|---|
| Bug found during review | back to **In Dev** | Comment: what failed, steps, expected vs actual, error text. Fix, re-run the gate, new report on the PR, back to In Review |
| Cause unclear | **Analysis**, then In Dev | Comment findings first |
| Big enough to be its own work | original stays **In Dev** | New Bug issue (same parent) that blocks the original |
| Bug found after the issue was closed | original stays closed | New Bug issue, "Found after #91" in its body; don't reopen |

### Other rules

- Move Status when the phase changes, not in a batch at the end. Tick checklist items in the body as they finish (**Edit body / tick boxes**), not only at the gate — the user reads the checklist first.
- Scope or decisions change → edit the **body** (append `## Scope updates`, newest last). The gap reviewer reads the body and the comments, but the body is the source of truth — put every decision there.
- **Plan changed during the work → write it back before the gate.** When the code needs a query, request, round trip or refresh the Query plan / Data loading plan doesn't have, add it to the body under `## Scope updates` (the row, the new counts, why) before the gate runs. Reviewers check the code against the body, so an unrecorded change fails review and a recorded one is checked against its reason.
- Work bigger than the issue → new sub-issues or tasks with blocked-by links, not silent scope growth.
- Abandoned work → comment the reason; ask the user whether to close it as not planned.
- Unrelated bug found → new Bug issue in the right repo; tell the user; don't fix it unasked.

## 5. Blockers

- Issue → issue: native blocked-by (**Blocked-by** in Commands). Before moving an issue to Analysis or In Dev, read its `blockedBy` (**Show one issue**); if a blocker is open (exception: orchestrated run, §7), don't start it — pick the next unblocked issue and tell the user what blocks what.
- Outside GitHub (waiting on the user, credentials, a decision, designs, a safe test setup, another team): add the label `blocked` (`gh issue edit <n> --add-label blocked`), comment exactly what is needed and from whom, leave the Status, and say so in the reply. Remove the label and comment when resolved.

## 6. Resuming and status questions

Read GitHub, not memory:

- A plan: **Plan tree** (status, open blockers) and **Waves** (what can start now).
- Waiting for review: **Board by status** with `In Review` (optionally one repo).
- Open work in a repo: `gh issue list -R Keyd-Solutions/<repo> --assignee @me --state open`.
- Report: waiting for review, in progress, blocked and by what, and the next unblocked issue.

## 7. Implementing a plan in parallel (orchestrated)

Trigger: "implement <plan>", "implement all the issues for X", "/github-issues implement <plan ref>".

The main session is the **orchestrator**: it owns GitHub tracking, merges, conflict fixing, the gate and end-to-end tests. Implementer subagents write code for one issue each and never touch tracking or start servers; gate subagents (Each wave, step 5) review or test `plan/<name>` and return a short result, and never touch tracking either.

### Before starting

1. **Plan tree** and **Waves** (with In Review blockers counted as satisfied). Skip closed issues. An issue whose body still says `_To be filled after analysis_`, has no **Files to touch** / **Mirror**, or touches data access without Query plan / Data loading plan tables (older issues), is not ready — do its analysis first (the In Dev hook refuses it anyway).
2. Waves come from blocked-by links: wave 1 = no open blockers inside the plan; wave N = blockers all in earlier waves. **Waves** shows what *can* run; when the PRD's Delivery order sequences work on purpose (e.g. "Android first"), follow it. Issues blocked by open issues outside the plan wait (tell the user). `user-task` issues are never dispatched — list them as the user's part of the run. If two issues in a wave will change the same files (per their work plan / technical notes), move one to the next wave. If two or more issues in a wave need the same **new** helper, component or query, one issue builds it first (or a small shared-pieces issue does) and the others wait for its merge — parallel agents can't see each other's code and would each write their own.
3. Working tree clean (`git status`). Base branch from §1. `git fetch`; if local base is behind or diverged from `origin/<base>`, tell the user first. Create the integration branch `plan/<name>` from the base and check it out in the main working tree.
4. Confirm a safe end-to-end setup (local/test DB and services). If missing, tell the user before any code is written.
5. **Context budget.** An orchestrated run is launched with `claude --autocompact 400k` (window range 100k–1M; Claude Code 2.1.296+; subagents inherit it), or each wave runs in a fresh session that resumes from the plan issue's last handoff comment. Without it the main thread climbs to ~1M before compacting and every turn re-reads that. If the session was not launched that way, say so in the run plan and keep the handoff comments (Each wave, step 8) anyway.
6. Show the run plan and **wait for the user's go**: waves (refs + titles), agents (max 4 in parallel), base and integration branch, test setup, and every step that will need the user (migrations, secrets, designs, accounts).

### Each wave

1. Status → **In Dev** for the wave's issues.
2. Launch one subagent per issue **in a single message** (parallel): `Agent` with `isolation: "worktree"`, `model: "sonnet"` and `effort: "xhigh"` (backend, data access, migrations or several files) or `effort: "high"` (UI-only or small single-file issues), max 4 at a time, prompt = template below. For an issue in another repo, the orchestrator creates `plan/<name>` there and the agent makes its own worktree: `git -C <repo> worktree add ../<repo>-<n> -b <n>-<slug> plan/<name>`.
3. For each DONE result, merge its branch into `plan/<name>` immediately. Keep the agent's short return in the main thread; never paste its diff or logs.
   - **Conflicts are always fixed, never left behind.** Resolve them in the orchestrator, reading both sides and the two issues' specs. If the right resolution isn't clear from the code and specs, send the conflict to a fix agent for that issue (same model and effort as its implementer), then merge again.
   - After a clean merge (and the repo's build still compiling), **remove the worktree and delete the issue branch**: `git worktree remove <path>` and `git branch -d <n>-<slug>` — the commits live on in `plan/<name>`.
   - Comment on the issue: merged commits, files, the agent's check results. **Tick that issue's Work plan steps the merge delivered** (agents never touch GitHub, so nobody else will).
   - The agent's return lists plan deviations → write each into the issue body under `## Scope updates` (row, counts, why) before the wave's gate (§4 Other rules).
4. **Coverage check (no agent):** `git diff --name-only <pre-wave commit>..plan/<name>` against each issue's **Files to touch** — a `✓/✗` table per issue (`[NEW]` must show under `--diff-filter=A`, `[DEL]` under `--diff-filter=D`). `✗` means "look here", not "failed"; pass the table to the gap review.
5. Run the **verification gate** (§4) on `plan/<name>` for the wave: automated checks (failures and summary lines only, e.g. `| tail -40`, never full logs); one `gap-review` over all the wave's issue numbers with the pre-wave commit as base (plus the coverage table); one `repo-security-review` of the wave's diff (same when-to-run rule); one `query-review` of the wave's diff with the wave's issue numbers, then the measured counts (same when-to-run rule); then the end-to-end test of every issue in the wave. Gate steps that produce long output (gap review, security review, query review, end-to-end) run in subagents on `plan/<name>` (no worktree; tracking stays with the orchestrator) and return at most ~15 lines: verdict, each ❌/⚠️ with file:line, evidence per acceptance criterion.
6. Passed → gate step 6 (Checklist) for each issue, open/refresh the plan PR (`plan/<name>` → base) with the wave's verification report, comment on each issue, Status → **In Review** with `# open-boxes: N`. Failures or ❌/⚠️ → stay **In Dev**, comment them, dispatch a fix agent in a new worktree (same model and effort as the issue's implementer, prompt = the template plus the findings), merge, re-run the gate (max 2 fix rounds per issue, then label `blocked` and tell the user).
7. BLOCKED / FAILED → label `blocked` + comment exactly what is needed. Its dependents don't start; everything else continues.
8. **Wave handoff:** comment on the plan issue — wave number, issues and statuses, merged commits, gate results, open problems, next wave. The plan issue is the run's memory: after a compaction only a ~3–6k-token summary survives.
9. Next wave. In an orchestrated run, a blocker counts as satisfied once it is merged into `plan/<name>` and passed the gate (In Review) — the **Waves** query as written.

If the user said "pause after each wave", stop after step 8 and report.

### End of the run

1. Final gate on `plan/<name>` vs the base: checks, `gap-review` with the plan issue number (PRD; the reviewer also reads its sub-issues), `repo-security-review` of the full diff, `query-review` of the full diff with the plan issue number plus the measured counts, and a full end-to-end run of the plan's main flow.
2. Verification report on the plan PR; plan issue → In Review.
3. Reply with a table: issue, status, merged commits, gate results, what each blocked issue needs.
4. Never merge `plan/<name>` into the base branch, push to protected branches, or deploy unless the user asks. Issues close only per §4 Closing.
5. No worktrees or merged issue branches are left behind (`git worktree list` shows only the main tree).

### Subagent prompt template

```
You are implementing GitHub issue <repo>#<n>: <title>
Repo: <path>. You are in your own git worktree, branched from plan/<name>. Work on the branch <n>-<short-slug>.

Issue body (the spec):
<full body: goal, covers, context, scope, design, data loading plan, query plan, docs checked, work plan, acceptance criteria, how to verify>

Already merged into your base: <ref – title of each completed blocker>
Running at the same time (stay out of their scope): <ref – title, ...>

Rules:
- Implement only this issue's scope. Follow the repo's CLAUDE.md, its review rulebooks `.claude/review/gap-rules.md` and `security-rules.md` (if present — the gate reviews against them), and the conventions of neighbouring code. Start from **Files to touch** and copy the shape of **Mirror**; touching another file is fine when needed — list it under Notes.
- Check the installed versions and the current docs for every library/platform API you use (node_modules types, official docs); never guess an API.
- Data access: implement the issue's **Query plan** and **Data loading plan** as written. First find out what this package uses (gap-rules.md → Data access, else its manifest/lockfile and the stack checklists' Detect lines — never assume a stack). Before writing any query, open the schema for the models involved and use their relations; follow `~/.claude/skills/data-access/SKILL.md` and the **Data access** sections of the matching stack checklists (`~/.claude/skills/review-rules/stacks/`). No query inside a loop, no `await` after `await` for independent calls, no loading a parent only to read an id you already have, no child request waiting for data the route already has. Frontend: the route's loader is the page's data list — components read from the cache and fetch only on a user action; nothing for closed dialogs, hidden tabs or other pages; saves update the cache from their response and invalidate exact keys; no `useEffect` to fetch or refetch. Mirror a peer's structure, not its waterfall. A query or request that isn't in the plan, or more sequential calls than planned → list it under Notes with why.
- Reuse before building: call what your issue's **Reuse** section lists; `grep` for an existing helper, component or query before writing one; never copy a function and change it slightly. If you built something other issues could share, name it under Notes.
- Do not read or update GitHub issues or the Project; the orchestrator does that.
- Run the repo's typecheck / lint / unit tests for what you changed. Do not start servers or run end-to-end tests.
- Reading (everything you read is re-read on every later turn):
  - Files under ~300 lines may be read whole. Larger files: `grep -n` for the symbol first, then read only that range (Read with offset/limit, or `sed -n 'A,Bp'`).
  - Don't re-read a file you already read unless it changed since.
  - `git diff --stat` before any full diff; then diff only the files you need.
  - Test and build output: failures and the summary only (e.g. `go test ./pkg/... 2>&1 | grep -E '^(--- FAIL|FAIL|ok|panic)' | head -60`, `| tail -40`). Cap any long output with `| head`.
- Commit on your branch as "<title> (#<n>)". Do not push, merge, deploy, edit .env files, or run migrations or scripts against any real database.
- If a step needs one of those, or something you don't have (credentials, a decision, designs), stop and report BLOCKED with exactly what is needed.

Return:
STATUS: DONE | BLOCKED | FAILED
Branch and commit hash(es)
Files changed
Checks: each command run and its result
Acceptance criteria: each one ✅ or ❌ with a one-line reason (from code and checks; end-to-end comes later)
Query plan / Data loading plan: "as planned", or each deviation with why
Notes for the reviewer
Keep the whole return to ~15 lines plus one line per acceptance criterion — no diffs, no logs.
```

## 8. Reference

`reference.md` next to this file holds the **Known gaps** (no GitHub Actions — run checks locally; board quirks; `gh issue delete` needs admin) and **Moving a repo's tickets from Jira**. Read it when one of those comes up.
