# Claude Code work system: GitHub Issues + global reviewers + data access

How work is tracked (the `github-issues` skill), how the global review system checks every change before it
goes to review (`review-rules`, `gap-review`, `repo-security-review`, `query-review` and their agents), and how
Claude is kept from writing waterfall / N+1 queries (`data-access`).

Built 2026-11-03. Everything described here is in this folder.

---

## 1. The big picture

```
                ┌──────────────────────────────────────────────────┐
 You ask for ─► │ github-issues skill (tracks the work)            │
 a job          │ issue → Analysis → In Dev → gate → In Review     │
                └───────┬──────────────────────────────────────────┘
                        │ verification gate, steps 2, 3, 4
       ┌────────────────┼──────────────────────┬─────────────────────────┐
       ▼                ▼                      ▼                         ▼
 while coding:     gap-review           repo-security-review        query-review
 data-access        └► gap-reviewer       └► security-reviewer        └► query-reviewer
 skill + CLAUDE.md     (agent)               (agent)                     (agent)
       │                │                      │                         │
       └────────────────┴───────── all read ───┴─────────────────────────┘
                ┌──────────────────────────────────────────────────────────────┐
                │ <repo>/.claude/review/gap-rules.md + security-rules.md       │
                │ (written once per repo by review-rules from the code;        │
                │  you confirm)  + the plugin's review-rules/stacks/*.md      │
                └──────────────────────────────────────────────────────────────┘
```

- **Skills** = instructions: *how* something is done. Shipped in the plugin's `skills/`.
- **Agents** = workers that run in a fresh, read-only context, only when a skill starts them. Shipped in the plugin's `agents/`.
- **Rules files** = the facts of one repo. Live inside each repo, committed to git.
- **Stack checklists** = generic checks and code patterns per technology; a repo loads only the ones it uses.

The **method** is the same for every repo; the **rules** are different for every repo. Every piece first
detects what the repo actually uses — nothing assumes Prisma, RTK Query or any other library.

---

## 2. github-issues: how work is tracked

File: `skills/github-issues/SKILL.md` (+ `reference.md`).

### Where work lives
- All work is a GitHub issue in org **Keyd-Solutions**, on the Project board **"Keyd Work"**.
- Repo work → the product's repo (table in §1 of the skill: nexafon, pms, new-resto, Resto, medly, influencer-ecommerce-, Keydsolutions-tools).
- Non-repo work (skills, tooling, home folder) → `Keydsolutions-tools`.
- No Jira (retired 2026-10-26) and no plan/TODO files — the plan lives in issues.
- No issue for questions, chat-only discussion or one-line trivial edits.

### Size of the job
| Size | Structure |
|---|---|
| Single job | One **Task** or **Bug** issue; steps as a checklist in the body |
| Big plan | **`[Plan] <name>`** Feature issue (body = PRD) → optional sub-features → **Task** children (body = spec), linked with native **blocked-by** dependencies |

### What an issue contains
- **Plan (PRD):** Problem & goal, Users & flows, Requirements (R1, R2…), Out of scope, Success measures, Decisions, Delivery order, Risks, Verification.
- **Task (spec):** Goal, Covers (R-numbers), Context, Scope In/Out, Files to touch, Mirror, Reuse, Design (data model, API, UI, **Query plan**, **Data loading plan**, docs checked), Work plan `- [ ]`, Acceptance criteria `- [ ]`, How to verify.
- **Query plan / Data loading plan are required** whenever the issue adds or changes a query, model, data endpoint or screen data loading — written before any code (see §4).
- Scope changes are appended to the body as `## Scope updates` (they outrank the older text).

### Status flow (on the board)
```
To Do ─► Analysis ─► In Dev ─► (verification gate) ─► In Review ─► Done
planned   reading,    coding;    must pass all 6 steps   PR open with    user
          designing   stays here                         the report      approves
```
- Branch per issue: `gh issue develop <n> --base <base branch>`; commits `… (#<n>)`.
- An issue that touches data access doesn't move to In Dev without its Query plan / Data loading plan.
- A hook refuses **In Review** while the issue still has unticked boxes, unless the count of intentionally open boxes is stated.
- A second hook refuses **In Dev** while the body still says `_To be filled after analysis_` or has an empty Query plan / Data loading plan, so data access is always planned before code.
- A plan change during the work is written back into the issue (`## Scope updates`) before the gate; older issues get their Query plan / Data loading plan tables before they start.
- Claude closes an issue only after you approve.
- Problems found in review → back to In Dev; bigger ones → a new Bug issue that blocks the original.

### The verification gate (before In Review)
0. **Review rules exist?** If `<repo>/.claude/review/*-rules.md` is missing → run `review-rules` first.
1. **Automated checks** — the repo's own typecheck / lint / tests.
2. **Gap review** — `gap-review` with the issue **number(s)** and the base commit.
3. **Security review** — `repo-security-review` when the change touches auth, input, DB, payments, uploads, secrets/config or dependencies.
4. **Query review + measured counts** — when the change touches data access: (a) `query-review` (waterfalls, N+1, unused relations, plan compliance); (b) statements per request from the query log with 1 row and 20 rows must equal the Query plan; screens' requests start together.
5. **End-to-end test** — real app, local/test data only (never production).
6. **Checklist** — tick boxes that have evidence; list the rest under "Please check".

The PR description is the verification report (what was tested, results incl. *planned → measured* query
counts, what you still need to check).

### Big plans in parallel (orchestrated runs)
Waves come from the blocked-by links. Each wave: up to 4 implementer agents in separate git worktrees →
merge into `plan/<name>` → coverage check → the same gate over the whole wave (one gap review, one security
review, one query review over all the wave's issue numbers) → In Review → handoff comment on the plan issue →
next wave. A final gate runs over the whole plan. Implementer agents read the repo's rules files and the
issue's Query plan before coding, so they avoid violations instead of only being caught.

---

## 3. The global review system

### Files

| Piece | Path | Job |
|---|---|---|
| `review-rules` skill | `skills/review-rules/SKILL.md` | Learns a repo once and writes its two rules files |
| Rules templates | `skills/review-rules/templates/` | The layout of `gap-rules.md` and `security-rules.md` |
| Stack checklists (13) | `skills/review-rules/stacks/` | node-express, prisma, mongoose, sql-raw, go, react-vite, nextjs, firebase, expo, better-auth, socket-io, payments-webhooks, uploads-s3 |
| `gap-review` skill | `skills/gap-review/SKILL.md` | Coordinator: checks inputs + rules, starts `gap-reviewer`, relays the report |
| `repo-security-review` skill | `skills/repo-security-review/SKILL.md` | Same for `security-reviewer` |
| `query-review` skill | `skills/query-review/SKILL.md` | Same for `query-reviewer`, then runs the query-count measurement; `--audit <path>` for existing code |
| `data-access` skill | `skills/data-access/SKILL.md` | How to write queries and data loading; Query plan / Data loading plan formats |
| `gap-reviewer` agent | `agents/gap-reviewer.md` | Sonnet, read-only. "Did we build what the issue promised, following the repo's rules?" |
| `security-reviewer` agent | `agents/security-reviewer.md` | Opus, read-only. "Can this diff be exploited?" |
| `query-reviewer` agent | `agents/query-reviewer.md` | Opus, read-only. "Does this make more round trips, queries or waiting than needed?" |

Each stack checklist has up to five parts: **Detect** (how to know the repo uses it), **Discovery** (what
`review-rules` must find out), **Gap checks**, **Security checks**, and **Data access** (✗/✓ code patterns).

### How a repo's rules are created — `/review-rules` (once per repo)
1. **Detect stacks per package** from `package.json`, `go.mod`, `firebase.json`, `schema.prisma`, … and record installed versions from the lockfiles.
2. **Read curated knowledge:** CLAUDE.md, convention docs, and any old reviewer agents in the repo (their rules are carried over).
3. **Gather evidence** in a read-only subagent: answers every Discovery question of the detected stacks, lists every route with its middleware, opens 2–3 peer files per kind to learn layout and registration points. Each finding is
   - **FACT** — proven by code (file:line),
   - **GUESS** — likely, needs your confirmation,
   - **ASK** — can't tell.
4. **You confirm** the GUESS/ASK items: tenancy, which unauthenticated routes are meant to be public, the threat model (3–5 worst outcomes). A route you say should *not* be public is a live bug.
5. **Write** `<repo>/.claude/review/security-rules.md` and `gap-rules.md`. Every rule cites its source; sections with no evidence say `N/A — <what was searched>`; unconfirmed items say `UNCONFIRMED`.
6. **Commit** the two files (so teammates and cloud sessions get them).

Each file header records `Built from: <commit> <date>`, `Stacks: …` and `Refresh when changed: <files>`.
A stack with no checklist still gets rules: its APIs are taken from the installed version's docs and written
into the rules file with their source.

### What's in the rules files
- **security-rules.md:** threat model · tenancy (MULTI / SINGLE / N/A) · authentication · authorization (guards) · public-route allow-list · input validation · data layer · webhooks/payments/uploads/real-time · secrets · must-flag changes.
- **gap-rules.md:** MUST/NEVER rules from the docs · tooling commands · layout · registration points · shared places to reuse · conventions · **data access per package** (ORM + version, eager-load behaviour, batch / transaction / parallel APIs, query log switch, shared selects, frontend data layer + loaders) · tests.

### How a gap review runs (example: influencer-ecommerce-#42 "Add coupon export")
```
1. Gate step 2 → gap-review skill: repo root, issue #42, base a1b2c3
2. Skill: gap-rules.md exists? (no → review-rules first) → starts gap-reviewer
3. gap-reviewer agent (fresh, read-only):
   a. gh issue view 42 --json body,comments   ← reads the issue itself, incl. scope updates
   b. reads .claude/review/gap-rules.md         ← repo facts
   c. loads the stacks listed there (Gap checks) ← node-express, prisma, react-vite
   d. git diff a1b2c3..HEAD                      ← ground truth, not the implementer's claims
   e. marks each work-plan step / acceptance criterion ✅ ⚠️ ❌,
      checks repo rules + stack checks + universal rules (no TODO, no any, DRY, registration)
   f. diff touched a "Refresh when changed" file → reports "Rules to refresh"
4. Report: ❌ permission missing in seeder → NEEDS_FIXES + the exact fix
5. Fix → review again → PASS → next gate step
```
The security and query reviews work the same way with their own rules and checklist sections.

### Who reads and writes what
| | Reads | Writes |
|---|---|---|
| `review-rules` | code, docs, old agents, stack Discovery | the two rules files (after you confirm) |
| review skills | only checks the rules files exist | nothing |
| reviewer agents | issue, diff, rules file, stack checklists | nothing (read-only) |
| `data-access` skill / implementers | rules file → Data access, stack Data access sections, schema | the code + the issue's Query plan |
| github-issues | the reviewers' verdicts | issue status, comments, PR report |
| You | the rules drafts and later refreshes | approvals, corrections |

### Keeping rules current
When a diff touches a file listed under `Refresh when changed`, or adds a pattern the rules don't describe
(new auth method, new webhook, new tenant column, new data library), the reviewer lists it under **Rules to
refresh**. Then `/review-rules --section <name>` updates just that section and shows you the change first.
`/review-rules --rebuild` starts over.

---

## 4. Data access: use the relations, no waterfalls, no N+1

### The problem
- **Waterfall** — `user = await getUser(id)` then `posts = await getPosts(user.id)`: the second call waited for an id it already had. Detail page: load the post, then load its author by `post.authorId`.
- **N+1** — load a list, then one query per row (`for (p of posts) p.author = await getUser(p.authorId)`).
- **Wasted requests** — a page calls endpoints it doesn't show: data for closed dialogs, hidden tabs or other pages, the same data twice, polling nobody looks at, a whole list loaded to show one name.
- All of them look fine with 3 rows of local data and slow down in production.

Why Claude wrote it that way: it chained existing single-record helpers ("reuse"), copied peer code that had
the same pattern, didn't open the schema to see the relation, let each component fetch its own data, and
nothing independent checked it.

### How it's stopped — one rule set, enforced at every stage
| Stage | Piece | What it does |
|---|---|---|
| Always loaded | `CLAUDE-data-access-section.md` (SessionStart hook) | 8 short rules in every session, even outside the issue flow |
| While writing | `data-access` skill | detect the repo's stack → read the schema → pick the shape → write the plan → code → check |
| Per technology | stack checklists → *Data access* | ✗/✓ code for Prisma, Mongoose, SQL, Go/pgx, Firestore, Express, React (RTK/TanStack/react-router), Next.js, Expo |
| Per repo | `gap-rules.md` → *Data access* | that repo's ORM + version, how its eager-load runs, batch/transaction/parallel APIs, query log switch, data layer |
| In the issue | **Query plan** + **Data loading plan** | required before In Dev; states every query and how many sequential calls it makes |
| While coding | implementer rules | implement the plan as written; any extra query or call listed with why |
| Gate step 4a | `query-review` → `query-reviewer` | independent check: waterfalls, unused relations, N+1, check-then-act, unbounded lists, missing indexes, plan compliance |
| Gate step 4b | query log | statements per request with 1 row and 20 rows = the plan; screens' requests start together |

### It adapts to each repo
Claude finds the stack in this order, per package:
1. the repo's `gap-rules.md` → Data access (built by `/review-rules` from the code);
2. otherwise the package's manifest + lockfile, matched against the checklists' **Detect** lines;
3. a library with no checklist (Drizzle, TypeORM, Django, Laravel, SWR, GraphQL…) → the universal rules plus
   that library's own API for the installed version, from its docs — and recorded in the repo's rules file.

So each of your repos gets its own patterns: Prisma 6 + RTK Query (influencer-ecommerce-, medly, pms),
Prisma 6 + TanStack Query (support-hub), Prisma + Mongoose + Firebase + Next (new-resto), Mongoose + Firebase +
Next (resto-), Go pgx + TanStack Query/Router + Next (nexafon).

### What the issue contains (examples in Prisma syntax — each repo uses its own)
**Query plan**
| Endpoint / function | Returns | Query shape | Sequential DB calls | Statements | Indexes |
|---|---|---|---|---|---|
| `GET /users/:id/profile` | user + 20 latest posts + count | `user.findUnique({ where: { id }, select: { …, posts: { take: 20, orderBy: … }, _count: … } })` | 1 | 2–3, same for 1 and 20 posts | `Post(userId, createdAt)` |
| `GET /posts/:id` | post + author | `post.findUnique({ where: { id }, include: { author: { select: { id, name, avatar } } } })` | 1 | 2 | — |

**Data loading plan**
| Screen / route | Requests | Inputs | Starts | Waits for |
|---|---|---|---|---|
| `/posts/:id` | `GET /posts/:id` (author included) | route param `id` | on navigation | — |

Rules: *Sequential DB calls* above 1 only with a reason (a value only an earlier call returns, e.g. the id of
a row just created); *Statements* must not grow with the rows; *Waits for* empty unless another response
really provides the input.

### Bad → good (Prisma example)
```ts
// ✗ waterfall: posts waits for user, but user.id === id
const user  = await prisma.user.findUnique({ where: { id } })
const posts = await prisma.post.findMany({ where: { userId: user.id } })

// ✓ one query through the relation
const user = await prisma.user.findUnique({
  where: { id },
  select: { id: true, name: true, posts: { select: { id: true, title: true }, orderBy: { createdAt: 'desc' }, take: 20 } },
})

// ✗ detail page: post, then author
const post   = await prisma.post.findUnique({ where: { id } })
const author = await prisma.user.findUnique({ where: { id: post.authorId } })

// ✓ include the author
const post = await prisma.post.findUnique({
  where: { id },
  include: { author: { select: { id: true, name: true, avatar: true } } },
})
```
```tsx
// ✗ frontend waterfall: posts waits for user although the route has the id
const { data: user }  = useGetUserQuery(id)
const { data: posts } = useGetPostsQuery(user?.id ?? skipToken)

// ✓ both start together from the route param (or one /users/:id/profile endpoint)
const { data: user }  = useGetUserQuery(id)
const { data: posts } = useGetPostsQuery(id)
```

### Frontend structure: the route is the page's data list
Most wasted requests come from one habit: every component fetches its own data when it renders, so nobody
owns the page's total list of requests. The fix is a structure where each layer has one job:

| Layer | Its job | Not its job |
|---|---|---|
| API client (often generated, e.g. orval) | one function per endpoint | caching, deciding when to call |
| Query definitions (e.g. `features/<x>/queries.ts`) | one definition + key per resource, and how it stays fresh | being re-declared under other keys |
| **Route / page** (loader, server component, screen hook) | **the page's data list**: every request, started together before render | rendering |
| Components | render data from the cache; fetch only on a user action | deciding the page's data |
| Shell / layout (every page) | only small data every page shows: session, workspace, access, badge counts | heavy lists, polling for one field |

**The 7 rules** (in `CLAUDE.md`, the `data-access` skill and the stack checklists):
1. **The route is the page's data list** — every request declared in the route loader (or the stack's equivalent) and started together; hovering a link then starts the data too.
2. **Components read; they don't fetch** — a component requests something only on a user action (open, expand, click, debounced typing).
3. **Only what's on screen** — nothing for closed dialogs, hidden tabs, collapsed panels or other pages; the shell stays small.
4. **One definition per resource** — one query key per resource, reused everywhere; no direct `fetch`.
5. **Refresh on purpose** — `staleTime`, a realtime event or polling while shown; saves update the cache from their response and invalidate exact keys; a realtime event updates **or** invalidates, never both.
6. **`useQuery` for server data, `useEffect` only for outside systems** (sockets, timers, browser APIs) — never to fetch, never to refetch after a user action, never to copy data into state.
7. **Endpoints shaped for the screen** — related names come with the data; never load a whole list to turn ids into names.

**Names for wasted requests:** over-fetching (data not shown) · eager fetching (closed/hidden UI, other pages) ·
chatty screen / under-fetching endpoints (many endpoints for one view) · redundant requests (same data twice) ·
over-polling / over-refetching · over-invalidation · thundering herd (one event → every user refetches) · frontend N+1.

**What the issue says before code** — the Data loading plan is the page's complete request list:

| Screen / route | Loader starts (together) | Inputs | On user action | Not loaded here | Waits for (why) | Refresh |
|---|---|---|---|---|---|---|
| Shell (every page) | session, workspace, access, unread count | cookie, slug | notification list (open the bell) | member directory, call lists | — | realtime updates the cache |
| `/billing?tab=wallet` | wallet, payment options, bank transfer, payment methods, ledger page 1 | workspace id, `tab` | quote (after choosing a provider), receipt PDF (click) | pricing, subscription, usage | quote — needs the provider | wallet via realtime; rest `staleTime` 60 s |

| Save | Cache update | Invalidates (exact keys) |
|---|---|---|
| Top-up | `setQueryData(wallet)` from the response | ledger, invoices — once |

Any other request on the screen is a finding. The gate's network-log check fails on anything extra, any
duplicate, or anything re-sent on window focus that the plan doesn't list.

### Finding existing waterfalls
`/query-review --audit <path>` reviews existing code (not a diff) and lists waterfalls and N+1s per
endpoint/screen; it offers to open issues for them and doesn't fix anything unasked.

---

## 5. Our security review vs. the built-in `/security-review`

| | Built-in (Anthropic) | `repo-security-review` |
|---|---|---|
| Knows your repo | No — generic every run | Yes — reads the repo's `security-rules.md` |
| Public routes | Guesses | Checked against your confirmed allow-list |
| Tenancy | Unknown | Tenant-filter or ownership checks, per repo |
| Stack depth | General | Loads only the repo's stack checklists |
| Base branch | Not documented | Resolves a base that shares history |
| Editable / learns | No | Yes — skill, agent, checklists, rules file |
| Setup | None | `/review-rules` once per repo |

Example: `findUnique({ where: { id } })` on an Order looks fine to a generic reviewer; ours knows Order is
store-owned and must filter `storeId` → CRITICAL tenant leak. The built-in remains a quick second opinion.

---

## 6. Installing

This folder is the Claude Code plugin **`review-system`**; the repo root is its marketplace (`keyd-tools`).

```
/plugin install review-system --marketplace abdinasir-Tman/claude-skills-hooks-agents
```

or `claude plugin marketplace add abdinasir-Tman/claude-skills-hooks-agents` then
`claude plugin install review-system@keyd-tools`. Run `/reload-plugins` or start a new session.

The plugin brings the skills (`/review-system:<skill>`), the agents (`review-system:<agent>`), both status hooks
(`hooks/hooks.json`) and a SessionStart hook that adds `CLAUDE-data-access-section.md` to every session — nothing
to copy and no `settings.json` or `CLAUDE.md` edits.

Then, in each repo: `/review-system:review-rules` → confirm the questions → commit `.claude/review/`.

Notes:
- Skills and agents find their bundled files through `${CLAUDE_PLUGIN_ROOT}`, so keep the folder layout as it is.
- In a repo that has its **own** `.claude/agents/gap-reviewer.md` or `security-reviewer.md`, run `/review-system:review-rules` there (it carries the old content over), then delete the old repo agents.
- An older manual install in `~/.claude/skills`, `~/.claude/agents`, `~/.claude/hooks` (plus its `settings.json` hook entries and the `CLAUDE.md` section) should be removed, or everything loads twice.
- `github-issues` is specific to the Keyd-Solutions org and its board; the review and data-access skills work in any repo.
