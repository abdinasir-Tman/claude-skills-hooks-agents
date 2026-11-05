# Stack: go (net/http, chi, gin, echo, fiber)

Detect: `go.mod`.

## Discovery
- Router and where routes are mounted (`chi.NewRouter`, `r.Route`, `r.Group`, `HandleFunc`); handler package layout (`internal/http/...`, `handlers/`).
- Auth middleware and how identity reaches handlers (context key, helper like `UserFromContext`); JWT library and verification options.
- Public route groups vs authenticated groups.
- Validation approach (struct tags + validator, manual).
- Error handling helpers and logging library.
- Layering (handler → service → store/repo) from 2–3 peers.
- (data access) Store/repo methods that already batch (`= ANY($1)`, `pgx.Batch`), `errgroup` usage, query tracer setup.

## Gap checks
- Errors are handled or returned, never `_ =` dropped (except documented cases); errors wrapped with `%w` where peers do.
- `context.Context` passed through to DB and outgoing calls.
- New handler registered on the right group like its peers; tests next to peers if peers have them (`*_test.go`).

## Security checks
- New handler is inside an authenticated group unless on the public allow-list.
- JWT: algorithm pinned, expiry checked, secret from config — no `ParseUnverified`, no `none`.
- Ownership/tenant check on every load-by-ID.
- `http.MaxBytesReader` / size limits on bodies and uploads; timeouts set on servers and HTTP clients.
- No `os/exec` with user input; `filepath.Clean` + base-dir check on any user path.
- SQL rules from sql-raw.md.
- No secrets in logs (`log.Printf("%+v", cfg)` style dumps).

## Data access
Patterns the writer follows (data-access skill) and the query-reviewer flags. ✗ = don't, ✓ = do.
- ✗ independent `QueryRow`/`Query` calls one after another ✓ a `pgx.Batch` sent with `pool.SendBatch(ctx, b)` (one round trip), or `errgroup.WithContext` to run them concurrently.
- ✗ a query inside `for _, x := range rows` ✓ one query with `= ANY($1)` on the collected ids, then assemble with a map.
- ✗ handler calls `svc.GetUser(ctx, id)` and then `svc.ListPosts(ctx, user.ID)` when `id` comes from the URL ✓ run both concurrently, or add one store method with the JOIN.
- SQL patterns from sql-raw.md; pass `ctx` to every query.
