# github-issues — reference

Read on demand from SKILL.md. Known gaps change as tooling changes; the Jira move is only for repos still being migrated.

## Known gaps (as of 2026-10-19)

- **No GitHub Actions (user, 2026-10-15):** the org hit its Actions limit; automatic CI workflows are disabled in nexafon, Keydsolutions-tools and influencer-ecommerce- (deploy workflows kept). Run every check locally; never add or re-enable workflows or suggest Actions-based builds without the user's OK. Android builds run on this Mac; iOS waits for a Mac with Xcode.
- A new repo's issues are not added to the board automatically: create with `--project "Keyd Work"`, or add an older one with `gh issue edit <n> -R … --add-project "Keyd Work"`, then Set Status. Issues may also land in the user's personal "untitled project" (Backlog); ignore it — Keyd Work is the board. If the token ever loses the `project` scope, the user runs `! gh auth refresh -h github.com -s project -c` (device code goes to the clipboard; open https://github.com/login/device).
- Hooks: `~/.claude/hooks/github-in-review-checklist.py` (In Review needs the checklist) and `~/.claude/hooks/github-in-dev-ready.py` (In Dev needs a finished spec, incl. the Query plan / Data loading plan), both PreToolUse on Bash in `~/.claude/settings.json`.
- Gate reviewers are global since 2026-11-03: skills `gap-review` / `repo-security-review` / `query-review` run the agents `gap-reviewer` / `security-reviewer` / `query-reviewer` (`~/.claude/agents/`) against each repo's `.claude/review/*-rules.md` (built by `review-rules`). Old repo agents (`nexafon-*-reviewer`, influencer-ecommerce- and new-resto `gap-reviewer` / `security-reviewer`) are superseded: their content moves into the rules files on each repo's first `/review-rules`, then they can be removed (a repo change — ask first). The nexafon ones still read Jira, so don't use them.
- No issue forms or PR template in the repos yet, and only nexafon has PR CI; other repos need `ci.yml` (leave `deploy.yml` alone).
- `gh issue delete` needs repo admin, which this account lacks: close a mistaken issue as not planned (`gh issue close <n> --reason "not planned"`), remove its parent and board item.

## Moving a repo's tickets from Jira

Done for Nexafon on 2026-10-15 with the scripts in that session's scratchpad (export → plan → create). For the next repo: export its open tickets (description, comments, links) from Jira; create the issues parent-first with type, parent, priority, label `from-jira`, the Jira text with `AS-…` references rewritten to `#n`, Jira comments in a collapsed "History from Jira" section and a footer linking the Jira key; then add blocked-by links; keep Done tickets in Jira; then update the §1 table. Pace writes ≤ 60/min (GitHub allows ~80 content writes per minute and ~500 per hour).
