---
name: data-access
description: Write database queries and data loading like a senior engineer in whatever stack the repo uses — detect the repo's ORM/driver, data layer and versions first; on the backend read the schema and use its relations, one round trip per need, independent queries in parallel, no query inside a loop; on the frontend the route is the page's data list (loader), components read from the cache, only what's on screen, no request waterfalls and no wasted requests (over-fetching, eager fetching, duplicate requests, over-polling, over-invalidation); and write the Query plan / Data loading plan tables for an issue. Use whenever writing or changing a DB query or ORM call (Prisma, Mongoose, SQL/pgx, Firestore, Drizzle, TypeORM, Sequelize, any other), a model, relation or migration, an API endpoint that returns related data, a route/page or code that loads data in a page or screen (RTK Query, TanStack Query/Router, react-router loaders, Next.js server components, Expo, any other), cache refresh/invalidation or realtime cache updates; and when planning an issue that adds any of these.
---

# Data access

Three mistakes this skill exists to stop, in any stack:

- **Waterfall** — calls that run one after another although the later one doesn't need the earlier one's result. Time = the sum of every call's latency.
  `user = await getUser(id)` → `posts = await getPosts(user.id)` — `user.id` *is* `id`; the second call waited for nothing.
- **N+1** — one query for a list, then one more query per row. Time and database load grow with the number of rows.
  `for (const post of posts) post.author = await getUser(post.authorId)`
- **Wasted requests** — a page calls endpoints it doesn't show: data for closed dialogs, hidden tabs or other pages, the same data twice, polling nobody looks at, a whole list loaded to show one name.

All three pass every test with 3 rows of local data and slow down in production. Prevent them by construction.

The **rules** below are the same for every repo. The **syntax** always comes from the repo you are in — never assume Prisma, RTK Query or any other library.

## 0. Find out what this repo uses

In this order — stop at the first that answers:

1. **The repo's rules:** `<repo>/.claude/review/gap-rules.md` → **Data access**. Built by `review-rules` from the code, per package: database, ORM/driver and installed version, how it loads relations, batches, runs transactions and runs calls in parallel, the query log switch, the frontend data layer, where pages declare their data and the route to copy, what the shell may load, shared selects/helpers, intentional exceptions.
2. **No rules file:** detect now. Read the manifests of the package you're changing (`package.json` + lockfile, `go.mod`, `pyproject.toml` / `requirements.txt`, `composer.json`, `Gemfile`) and its schema files; compare with the **Detect** line of each `${CLAUDE_PLUGIN_ROOT}/skills/review-rules/stacks/*.md`, and load the **Data access** section of every match. Monorepos: each package can use a different stack — detect per package. Frontend: also find the best existing route that already declares its data (a loader that prefetches) and copy it.
3. **A stack with no checklist** (e.g. Drizzle, TypeORM, Sequelize, Knex, SQLAlchemy, Django ORM, Eloquent, ActiveRecord, SWR, Apollo): the rules below still apply. Look up that library's own API for the **installed version** — eager loading of relations, batching by ids, transactions, running queries in parallel, query logging; for a frontend library its route-level loading, prefetching, cache keys, invalidation and polling — from its types/README in the dependency folder, then Context7, then the official docs. Name the API and the doc source in the plan. Tell the user the checklist is missing; the next `/review-rules` records the patterns in gap-rules.md so they aren't looked up again.

Use the version you found: an API that isn't in that version's types or docs doesn't exist for this repo.

## 1. Procedure — before writing the code

1. **List what the endpoint / screen shows**: fields, related records, counts, pagination — and for a screen also what the user can do on it (dialogs, tabs, saves).
2. **Open the schema** for those models (the ORM's schema/model files or the SQL migrations) and note the relations between them. If two models are linked by a bare id column without a declared relation, declare it (foreign key + the ORM's relation definition) and index the FK column in the migration — don't work around a missing relation with extra queries.
3. **Pick the shape** from the table below; for a screen also apply the frontend structure (section 3).
4. **Write the plan rows** (formats in section 4), in the repo's own syntax — in the issue's spec when there is an issue; otherwise state them in the reply. For a screen the Data loading plan is the **complete** request list.
5. **Write the code** with the patterns from step 0.
6. **Check it** (section 5) before calling it done.

## 2. Pick the shape

"Eager-load" = the repo's API for loading a relation in the same call — e.g. Prisma `include`/`select`, Mongoose `populate`, SQL `JOIN` / `json_agg`, Drizzle `with`, TypeORM `relations`, Sequelize `include`, SQLAlchemy `selectinload`/`joinedload`, Django `select_related`/`prefetch_related`, Eloquent `with`, ActiveRecord `includes`.
"Run together" = the repo's parallel or batch primitive — e.g. `Promise.all`, Prisma `$transaction([...])`, `pgx.Batch`, Go `errgroup`, `asyncio.gather`.

| Need | Do | Not |
|---|---|---|
| A record and its related records (user + posts, post + author) | One query that eager-loads the relation | Load the record, then a second query by its id |
| Children of a parent whose id you already have (posts of user `:id`) | Query the children directly with that id; if the parent is shown too, eager-load the children with the parent, or run both together | Load the parent first only to read an id you already have |
| A check + the data (orders of a store I own) | Put the check in the same query — a relation filter / join condition (`store.ownerId = me`) | Load the store to check, then load the orders |
| A list with related data per row (posts with author name) | Eager-load the relation (one extra statement or a join for the whole list) | A query per row in a loop or `map` |
| A list + its total | List and count run together, or one statement (window function, facet) | `count` after the list, sequentially |
| Several independent things (dashboard tiles) | Run together | One `await` after another |
| Many writes | The bulk API (`createMany`, `insertMany`, multi-row `INSERT`, `bulkWrite`), nested writes, one transaction | A write per row in a loop |
| Change a row only if it belongs to the tenant/user | One statement with the scope in its filter, then check the affected-row count | Read, check in code, then write |
| The current user / tenant | Use what the auth/tenant middleware already attached to the request | Load the user again in the handler |
| A page / screen | The route declares every request in its loader (or the stack's equivalent) and starts them together from what is known at navigation (route params, session); components read from the cache; data always shown together comes from one endpoint | A component that fetches after its parent's data arrives, or only after its code chunk renders |
| A screen shows related names (creator, staff, plan) | The endpoint returns them (eager-load on the backend) | Load the whole members/staff/plans list to turn ids into names |
| A value only an earlier result provides (the id of a row just created, an external API response) | Sequential is correct — write the reason in the plan | — |

Always: select only the columns the caller uses (never whole user rows), paginate every list (limit + cursor or page), limit to-many relations in lists, index every FK and every column you filter or sort on.

### Reuse is not a reason for a waterfall

"Reuse before building" means reusing **query pieces** — shared select/projection objects, filter builders, the service that owns the model, the feature's query definitions. It does not mean chaining existing single-record helpers (`getUser()` then `getPosts()`) one after another. If the helper can't return the relation, give it an eager-load option or add one purpose-built query next to it in the same service.

### Mirror the structure, not the mistake

When a spec says "Mirror <peer>", copy its file layout and conventions. If the peer's data access breaks these rules (waterfall, N+1, wasted requests), don't copy that part — follow this skill and name the peer under Notes as a candidate fix.

## 3. Frontend structure — where data loading lives

Each layer has one job:

| Layer | Its job | Not its job |
|---|---|---|
| API client (often generated) | one function per endpoint | caching, deciding when to call |
| Query definitions (the repo's place, e.g. `features/<x>/queries.ts`) | one definition + key per resource, and how it stays fresh | being re-declared under other keys |
| **Route / page** (loader, server component, screen hook) | **the page's data list**: every request the page needs, started together before it renders | rendering |
| Components | render data read from the cache; start a request only on a user action | deciding the page's data |
| Shell / layout (on every page) | only small data every page shows: session, workspace, access, badge counts | heavy lists, polling a list to read one field |

### The 7 rules

1. **The route is the page's data list.** Every page declares every request it needs in one place that runs before it renders, and starts them together. TanStack Router: a `loader` (with `loaderDeps` for search params) that starts each query through the query client, using the **installed version's** API — TanStack Query 5.104 deprecates `prefetchQuery` / `ensureQueryData` / `fetchQuery` / `prefetchInfiniteQuery` in favour of `void queryClient.query(opts).catch(() => {})` (start it), `await queryClient.query({ ...opts, staleTime: 'static' })` (only when a later request needs its value) and `queryClient.infiniteQuery(opts)`; older v5 versions use `prefetchQuery` / `ensureQueryData`. Check the version's types before copying an existing loader — it may use the deprecated names. react-router: the route `loader`. Next.js: the page's server component. Expo: the screen-level hook. The repo's own pattern and the route to copy are in gap-rules.md → Data access. With link preloading on (e.g. TanStack `defaultPreload: 'intent'`), hovering a link then starts the data too, not just the code.
2. **Components read; they don't fetch.** They use the same query definitions the loader used (a cache hit, no new request). A component starts its own request only on a user action: opening a dialog, expanding a panel, clicking, typing (debounced).
3. **Only what's on screen.** Closed dialogs, hidden tabs, collapsed panels and other pages fetch nothing (`enabled: open`, or mount the content only when open). Shell components don't load lists to read one field — use a small endpoint, or `select` the field from data the page already has.
4. **One definition per resource.** One key per resource, reused everywhere — no second key for the same data, no direct `fetch` beside the cache.
5. **Refresh on purpose.** Every query states how it stays fresh: `staleTime`, a realtime event, or polling (only while shown; lists poll their first page only). A save updates the cache from its response (`setQueryData`) and invalidates only the exact keys it changed — never `invalidateQueries()` without a key. A realtime event either updates the cache or invalidates — never both; one change → one refresh; debounce bursts. Data that realtime keeps current doesn't refetch on window focus.
6. **`useQuery` / the loader for server data; `useEffect` only to sync with systems outside React** — sockets and call connections, timers, browser listeners, microphone/audio, focus/scroll, the URL, storage. Never fetch in an effect; never refetch or invalidate in an effect because of a user action (do it in the event handler or the save's `onSuccess`); never copy query data into state (derive it during render).
7. **Endpoints shaped for the screen.** When a screen shows related names or rows, the endpoint returns them. Never load a whole list (members, staff, plans) to turn ids into names; two requests always shown together → one endpoint.

### Wasted requests — names and fixes

| Name | What it looks like | Fix |
|---|---|---|
| Over-fetching | requests or fields the screen doesn't show | drop them; return only what's shown |
| Eager fetching | data for closed dialogs, hidden tabs, collapsed panels or other pages; speculative prefetches | fetch on open / on intent only |
| Chatty screen (endpoints that under-fetch) | one view needs many endpoints, or a whole list just for names | a screen-shaped endpoint with the relation included |
| Redundant requests | the same data twice: two keys, several observers polling, refetching what a save just returned, two triggers for one change | one key; `setQueryData` from the response; one trigger |
| Over-polling / over-refetching | polling while not shown, polling every loaded page of a list, refetch on focus for realtime-kept data, `staleTime: 0` causing a refetch per mount | poll only what's shown, first page only; per-resource `staleTime` |
| Over-invalidation | `invalidateQueries()` without a key, broad prefixes, invalidating what an event already updated | exact keys; update **or** invalidate |
| Thundering herd | one event makes every connected user refetch at the same moment | update the cache from the event's payload |
| Frontend N+1 | each row, card or media item fetches its own data | the list endpoint returns what rows show; one batch call |

## 4. Plan formats (the issue spec's Query plan and Data loading plan — github-issues §3)

**Query plan** — backend, one row per endpoint / function / job that reads or writes data. The Query shape is written in the repo's own syntax; the examples below happen to be Prisma.

| Endpoint / function | Returns | Query shape (model · filter · eager-load/select · order · limit) | Sequential DB calls | Statements | Indexes |
|---|---|---|---|---|---|
| `GET /users/:id/profile` | user (id, name, avatar), 20 latest posts, post count | `user.findUnique({ where: { id }, select: { id, name, avatar, posts: { select: {…}, orderBy: { createdAt: 'desc' }, take: 20 }, _count: { select: { posts: true } } } })` | 1 | 2–3, same for 1 and 20 posts | `Post(userId, createdAt)` |
| `GET /posts/:id` | post + author (id, name, avatar) | `post.findUnique({ where: { id }, include: { author: { select: { id, name, avatar } } } })` | 1 | 2 | — |

- **Sequential DB calls** — awaits on the request's critical path that wait for an earlier DB call. 1 = one query, one parallel group or one transaction. More than 1 needs a *why* (a value only the earlier call provides).
- **Statements** — what the query log shows per request. Some eager-load APIs add one statement per relation level instead of a join (the repo's rules or the stack checklist say which) — fine, as long as the number doesn't grow with the rows.

**Data loading plan** — frontend, one row per screen, plus one row for the shell (what every page loads):

| Screen / route | Loader starts (together) | Inputs | On user action | Not loaded here | Waits for (why) | Refresh |
|---|---|---|---|---|---|---|
| Shell (every page) | session, workspace, access, unread count | cookie, route slug | notification list (open the bell) | member directory, call lists | — | realtime events update the cache; no polling |
| `/billing?tab=wallet` | wallet, payment options, bank transfer, payment methods, ledger page 1 | workspace id (layout), `tab` (URL) | quote (after choosing a provider), receipt PDF (click) | other tabs' data: pricing, subscription, usage | quote — needs the chosen provider | wallet: realtime event updates the cache; the rest `staleTime` 60 s; no polling |
| `/posts/:id` | `GET /posts/:id` (author included) | route param `id` | comments page 2 (scroll) | — | — | `staleTime` 30 s |

**Saves** — one row per save on these screens:

| Save | Cache update | Invalidates (exact keys) |
|---|---|---|
| Top-up | `setQueryData(wallet)` from the response | ledger, invoices — once (not again from the realtime event) |

- The list is **complete**: a request on the screen that isn't in it — including one the shell adds — is a finding.
- **Inputs** must be known at navigation (route params, search params, session). A request whose input comes from another response goes under **Waits for**, with why.
- Two requests that are always shown together on one screen → one endpoint, unless they are cached and reused separately on purpose (say so).

## 5. Check it

Backend:
- For each request path, list the DB/API awaits in order: is any of them waiting for something it doesn't use?
- Search the change for a query or request inside a loop: `await` in `for` / `for…of` / `while` / `.map(` / `.forEach(`, `Promise.all(rows.map(… query …))` (still one query per row), and the equivalents in other languages. Every hit is a candidate N+1.
- Run it with the query log on and count statements per request with 1 row and with 20 rows — the two counts must match each other and the plan. The switch comes from gap-rules.md → Data access, else the stack checklist, else the installed library's docs (its logging / debug / tracer option, or the database's own statement log on a local server). No switch in the repo → say so and suggest adding one. Local or test data only.

Frontend — open each screen with the browser's network log:
- The planned requests start together on navigation (and on link hover where preloading is on).
- Nothing outside the plan: no other screens' data, no closed dialog's data, no duplicates; the shell adds only its planned row.
- Nothing is re-sent on window focus or tab switch unless the plan says so; polling only on screens that show it.
- Each save causes only its planned cache update / refresh.
- No `useEffect` in the change fetches, refetches or invalidates because of a user action, or copies query data into state.
