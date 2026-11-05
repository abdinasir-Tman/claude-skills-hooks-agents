# Stack: raw SQL (pg, pgx, sqlc, knex, database/sql)

Detect: `pg`, `postgres`, `knex`, `jackc/pgx`, `database/sql`, `sqlc.yaml`.

## Discovery
- Where queries live (sqlc `queries/*.sql`, repository files); how they are generated.
- Tenant/owner columns in migrations; whether Row Level Security is used.
- Migration tool and folder.
- (data access) Query log / tracer switch for local runs; existing batch helpers (`= ANY($1)`, batch sends); conventions for loading children (JOIN, `json_agg` subqueries).

## Gap checks
- New query added where peers keep queries (and sqlc regenerated if used).
- Migration added for schema change, with a down step if peers have one.

## Security checks
- Parameters always bound (`$1`, `?`, sqlc args); never string-concatenated or `fmt.Sprintf` into SQL. Dynamic `ORDER BY`/column names come from an allow-list.
- Tenant/owner filter in every query on tenant/owned tables (or RLS policy covers it and the connection sets the tenant).
- Transactions for multi-step money/stock changes; no check-then-act races on balances/stock without locking or atomic updates.

## Data access
Patterns the writer follows (data-access skill) and the query-reviewer flags. ✗ = don't, ✓ = do.
- ✗ `SELECT … FROM users WHERE id = $1`, then `SELECT … FROM posts WHERE user_id = $1` sequentially
  ✓ one statement: `SELECT u.id, u.name, (SELECT COALESCE(json_agg(t), '[]') FROM (SELECT id, title, created_at FROM posts WHERE user_id = u.id ORDER BY created_at DESC LIMIT 20) t) AS posts FROM users u WHERE u.id = $1` — or both queries sent together in one batch / in parallel.
- ✗ load the post, then `SELECT … FROM users WHERE id = <author_id>` ✓ `JOIN users a ON a.id = p.author_id` in the post query, selecting only the author columns needed.
- ✗ a query per row ✓ `WHERE id = ANY($1)` with the collected ids, or a JOIN.
- ✗ the list, then `SELECT count(*)` sequentially ✓ `count(*) OVER ()` in the list query, or both in one batch.
- ✗ `INSERT` in a loop ✓ a multi-row `INSERT … VALUES (…), (…)`, `INSERT … SELECT * FROM unnest($1::…[], …)` / `jsonb_to_recordset`, or `COPY` for bulk loads — but PostgreSQL doesn't support `COPY FROM` on tables with row-level security (use `unnest` / `jsonb_to_recordset` there; sqlc `:copyfrom` uses COPY).
- ✗ `SELECT` → check in code → `UPDATE` ✓ `UPDATE … WHERE id = $1 AND tenant_id = $2 RETURNING …` and check the affected rows.
- Index every FK column and every filter/sort column (PostgreSQL doesn't index foreign keys automatically); `EXPLAIN` new list queries on realistic data.
