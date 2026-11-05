# security-rules — <repo>

Built from: commit <sha> on <YYYY-MM-DD> · Confirmed by user: <YYYY-MM-DD | NOT YET>
Stacks: <comma list of ~/.claude/skills/review-rules/stacks/*.md names>
Refresh when changed: <paths whose change can invalidate these rules, e.g. schema, app entry, middleware dir, auth config, CLAUDE.md>

Every rule ends with `— source: <file:line | CLAUDE.md:line | peer inference (n files) | user YYYY-MM-DD>`.
Items still to confirm are marked `UNCONFIRMED`.

## Threat model
The 3–5 worst things that can happen in this repo, most severe first.
1. …

## Tenancy
MULTI | SINGLE | N/A
- Tenant column and owned models …
- How the tenant is resolved per request …
- Ownership (IDOR) rules for single-user records …

## Authentication
- Mechanism (session cookie / JWT / Firebase ID token / API key) and where it is verified …
- How handlers get the current user …

## Authorization
- Guards / RBAC middleware names and when each is required …
- Privileged roles and bypasses that are intentional …

## Public routes (allow-list)
Anything not on this list must require auth.
| Method | Path | Why public | Protection (signature, rate limit…) |
|---|---|---|---|

## Input validation
- Library, schema folder, how controllers call it …

## Data layer
- Raw SQL / unsafe query rules, mass-assignment rules, fields that must never leave the server …

## Webhooks, payments, uploads, real-time
(Sections that don't apply: `N/A — <evidence>`.)

## Secrets and config
- Secret names that must never be logged or returned …
- Env files: which are tracked (`.env.example`) …

## Repo-specific must-flag changes
- Changes that always get HIGH for human review (role assignment hooks, auth config, CORS, cookie flags…) …
