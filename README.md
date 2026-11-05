# claude-skills-hooks-agents

A ready-to-install set of **Claude Code skills, agents and hooks** that make Claude work like a careful senior
engineer on any repository:

- every job is **tracked in GitHub Issues** with a written plan before code is touched;
- every change passes a **verification gate** — gap review, security review, query review and an end-to-end test — before it goes to review;
- Claude **never writes request waterfalls or N+1 queries**, in whatever stack the repo uses (Prisma, Mongoose, raw SQL, Go/pgx, Firestore, React, Next.js, Expo, …).

It installs as one Claude Code plugin, **`review-system`**:

```
/plugin install review-system --marketplace abdinasir-Tman/claude-skills-hooks-agents
```

Everything lives in [`claude-review-system/`](claude-review-system/). Its own
[README](claude-review-system/README.md) is the full manual; this page is the map.

---

## Contents

- [What's in this folder](#whats-in-this-folder)
- [How the pieces fit together](#how-the-pieces-fit-together)
- [Skills](#skills)
- [Agents](#agents)
- [Hooks](#hooks)
- [Install](#install)
- [Using it](#using-it)
- [Customising for your own org](#customising-for-your-own-org)

---

## What's in this folder

```
.claude-plugin/
└── marketplace.json                   makes this repo a plugin marketplace ("tman")

claude-review-system/                  the "review-system" plugin
├── .claude-plugin/plugin.json         plugin name, version, author
├── README.md                          full manual (workflow, gate, data-access rules, examples)
├── CLAUDE-data-access-section.md      always-on rules, added to every session by a SessionStart hook
│
├── skills/
│   ├── github-issues/                 work tracking: issues, plans, statuses, verification gate
│   │   ├── SKILL.md
│   │   └── reference.md               known gaps, moving tickets from Jira
│   ├── review-rules/                  learns a repo once, writes its review rulebooks
│   │   ├── SKILL.md
│   │   ├── templates/                 layout of gap-rules.md and security-rules.md
│   │   └── stacks/                    13 per-technology checklists (see below)
│   ├── gap-review/SKILL.md            "did we build what the issue promised?"
│   ├── repo-security-review/SKILL.md  "can this diff be exploited?"
│   ├── query-review/SKILL.md          "any waterfalls, N+1s or wasted requests?"
│   └── data-access/SKILL.md           how to write queries and page data loading
│
├── agents/
│   ├── gap-reviewer.md                read-only reviewer started by gap-review
│   ├── security-reviewer.md           read-only reviewer started by repo-security-review
│   └── query-reviewer.md              read-only reviewer started by query-review
│
└── hooks/
    ├── hooks.json                     registers the hooks below
    ├── github-in-dev-ready.py         blocks "In Dev" until the issue spec is complete
    └── github-in-review-checklist.py  blocks "In Review" while checklist boxes are unticked
```

**Stack checklists** (`skills/review-rules/stacks/`): `node-express`, `prisma`, `mongoose`, `sql-raw`, `go`,
`react-vite`, `nextjs`, `firebase`, `expo`, `better-auth`, `socket-io`, `payments-webhooks`, `uploads-s3`.
Each one has up to five parts — **Detect**, **Discovery**, **Gap checks**, **Security checks**, **Data access**
(✗/✓ code). A repo only loads the checklists for the stacks it actually uses.

---

## How the pieces fit together

```
 You ask for a job
        │
        ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ github-issues   issue → Analysis → In Dev → gate → In Review │
 └──────┬──────────────────────────────────────────────────────┘
        │                         verification gate
        ├── while coding ──► data-access skill  (+ CLAUDE.md rules)
        ├── step 2 ────────► gap-review            ──► gap-reviewer agent
        ├── step 3 ────────► repo-security-review  ──► security-reviewer agent
        └── step 4 ────────► query-review          ──► query-reviewer agent
                                     │
                    all of them read │
                                     ▼
        <repo>/.claude/review/gap-rules.md + security-rules.md
        (written once per repo by /review-rules, confirmed by you)
        + the plugin's review-rules/stacks/*.md
```

| Kind | What it is | Where it lives |
|---|---|---|
| **Skill** | Instructions — *how* something is done | the plugin's `skills/` |
| **Agent** | A worker in a fresh, read-only context, started only by a skill | the plugin's `agents/` |
| **Hook** | A script Claude Code runs before a tool call or at session start; can refuse a call | the plugin's `hooks/hooks.json` |
| **Rules files** | The facts of *one* repo (threat model, conventions, data stack) | `<repo>/.claude/review/`, committed |
| **Stack checklists** | Generic checks and code patterns per technology | the plugin's `skills/review-rules/stacks/` |

The **method** is the same for every repo; the **rules** differ per repo. Nothing assumes a particular library —
every piece first detects what the repo actually uses.

---

## Skills

| Skill | Use it when | What it does |
|---|---|---|
| `github-issues` | Starting any code change, bug fix, feature or plan; asking "what's left?" | Creates Task/Bug/`[Plan]` issues with full specs, links blockers, moves the board status, runs the verification gate, writes the PR report, can run a plan in parallel waves with worktree agents |
| `review-rules` | Once per repo (`/review-rules`), or when a reviewer says rules are stale | Detects the stacks, gathers evidence from the code, asks you to confirm guesses, writes `.claude/review/gap-rules.md` and `security-rules.md` |
| `gap-review` | After implementing an issue | Runs `gap-reviewer` against the issue and the diff: missed, partial or silently changed work |
| `repo-security-review` | Change touches auth, input, DB, payments, uploads, secrets or deps | Runs `security-reviewer` with the repo's threat model: tenant leaks, auth bypass, injection, data exposure |
| `query-review` | Change touches queries, models, data endpoints or page loading; `--audit <path>` for existing code | Runs `query-reviewer`: waterfalls, N+1, unused relations, over-fetching, missing indexes, wasted frontend requests |
| `data-access` | Writing any query or page/screen data loading | Detect stack → read schema → use relations → plan the queries → code → measure |

## Agents

| Agent | Model | Question it answers |
|---|---|---|
| `gap-reviewer` | Sonnet, read-only | Did we build what the issue promised, following the repo's rules? |
| `security-reviewer` | Opus, read-only | Can this diff be exploited? |
| `query-reviewer` | Opus, read-only | Does this make more round trips, queries or waiting than needed? |

The agents are never called directly — the matching skill checks the inputs, starts the agent, and relays its
report. Because they run in a fresh context, the implementer never reviews its own work.

## Hooks

Both are `PreToolUse` hooks on `Bash`. They watch `gh project item-edit … --value "<status>"` commands:

| Hook | Refuses | Until |
|---|---|---|
| `github-in-dev-ready.py` | moving an issue to **In Dev** | the body no longer says `_To be filled after analysis_` and its Query plan / Data loading plan sections are filled |
| `github-in-review-checklist.py` | moving an issue to **In Review** | every `- [ ]` box is ticked, or the command states how many stay open on purpose: `# open-boxes: 2` |

---

## Install

This repo is a **Claude Code plugin marketplace**. One command installs everything — skills, agents, hooks and
the always-on data-access rules. No copying files, no editing `settings.json`.

**Inside Claude Code** (2.1.275 or newer):

```
/plugin install review-system --marketplace abdinasir-Tman/claude-skills-hooks-agents
```

Or in two steps (works on older versions too):

```
/plugin marketplace add abdinasir-Tman/claude-skills-hooks-agents
/plugin install review-system@tman
```

**From the terminal:**

```bash
claude plugin marketplace add abdinasir-Tman/claude-skills-hooks-agents
claude plugin install review-system@tman
```

Then run `/reload-plugins` (or start a new session). Done.

| Command | What it does |
|---|---|
| `claude plugin marketplace update tman` | fetch the latest catalog |
| `claude plugin update review-system@tman` | update the plugin |
| `claude plugin disable review-system@tman` | turn it off without uninstalling |
| `claude plugin uninstall review-system@tman` | remove it |
| `claude plugin install review-system@tman --scope project` | install for one repo only (shared with the team via `.claude/settings.json`) |

**Requirements:** the GitHub CLI **`gh` 2.102+** (issue types, sub-issues, blocked-by) and `python3` for the hooks.

### What the plugin sets up

| Piece | How it's loaded |
|---|---|
| 6 skills | `/review-system:<skill>`; Claude also picks them up automatically from their descriptions |
| 3 reviewer agents | `review-system:gap-reviewer`, `review-system:security-reviewer`, `review-system:query-reviewer` |
| Status hooks | `PreToolUse` on `Bash`, registered by [`hooks/hooks.json`](claude-review-system/hooks/hooks.json) |
| Data-access rules | a `SessionStart` hook adds [`CLAUDE-data-access-section.md`](claude-review-system/CLAUDE-data-access-section.md) to every session — no `CLAUDE.md` edit needed |

> **Already installed these by hand** in `~/.claude/skills`, `~/.claude/agents` and `~/.claude/hooks`? Remove
> those copies, their hook entries in `~/.claude/settings.json`, and the data-access section in
> `~/.claude/CLAUDE.md` — otherwise every skill, agent and rule is loaded twice.

### Try it without installing

```bash
git clone https://github.com/abdinasir-Tman/claude-skills-hooks-agents.git
claude --plugin-dir claude-skills-hooks-agents/claude-review-system
```

---

## Using it

1. **Once per repo** — open the repo in Claude Code and run:
   ```
   /review-system:review-rules
   ```
   Answer the questions it marks GUESS / ASK (tenancy, which routes are meant to be public, the worst things
   that could go wrong), then commit `.claude/review/`.

2. **For every job** — just ask for the work. Claude follows `github-issues`:
   ```
   To Do ─► Analysis ─► In Dev ─► verification gate ─► In Review ─► Done
             spec +      code      checks, gap,         PR with the    you
             query plan            security, query,     report         approve
                                   end-to-end test
   ```

3. **Run a review on demand**
   ```
   /review-system:gap-review 42                 # against issue #42
   /review-system:repo-security-review          # the current branch's diff
   /review-system:query-review                  # the current diff
   /review-system:query-review --audit src/     # find existing waterfalls / N+1s
   ```
   Or just ask — "review the security of this branch", "check this for N+1 queries" — and Claude picks the skill.

4. **Run a whole plan in parallel** — `/review-system:github-issues implement <plan issue>`: issues are grouped into waves by
   their blocked-by links, up to 4 agents work in separate git worktrees, each wave is merged and passes the gate
   before the next starts.

See [`claude-review-system/README.md`](claude-review-system/README.md) for the full gate, the Query plan /
Data loading plan formats, bad → good code examples, and how this compares to the built-in `/security-review`.

---

## Customising for your own org

`github-issues` is written for the **Keyd-Solutions** GitHub org and its "Keyd Work" project board. To use it
elsewhere, edit `skills/github-issues/SKILL.md`:

- **Constants** — org name, assignee, project number, Priority field and option IDs;
- **§1 Repos** — the table mapping local folders to GitHub repos and their base branches;
- the hooks' `IN_DEV_OPTION` / `IN_REVIEW_OPTION` — the Status option IDs of your board.

`review-rules`, `gap-review`, `repo-security-review`, `query-review` and `data-access` work in any repo with no
changes. To support a new technology, add a checklist to `skills/review-rules/stacks/` with the same five
sections.

To ship your changes: fork the repo, edit, bump `version` in `claude-review-system/.claude-plugin/plugin.json`
(installed copies only update when the version changes), check with
`claude plugin validate .`, and install from your fork.
