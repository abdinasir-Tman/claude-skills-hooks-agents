# Stack: nextjs

Detect: `next` dependency.

## Discovery
- App Router (`app/`) vs Pages Router (`pages/`); where API routes / route handlers / server actions live.
- `middleware.ts` matcher config and what it protects.
- Auth helper used in server components and route handlers.
- Data fetching pattern in server components.
- (data access) The data helpers server components call; caching / revalidation config; pages whose client components fetch what the server page could load; the best page to copy.

## Gap checks
- New route/page placed where peers are; metadata and loading/error files where peers have them.

## Security checks
- Every route handler and server action checks auth itself — `middleware.ts` matchers alone are not enough (paths outside the matcher, direct action calls).
- Server actions validate input; they are public POST endpoints.
- No secrets in `NEXT_PUBLIC_*`; server-only modules not imported into client components.
- `next.config` `images.remotePatterns` / rewrites don't allow arbitrary hosts (SSRF / open proxy).
- `dangerouslySetInnerHTML` rules from react-vite.md.

## Data access
Patterns the writer follows (data-access skill) and the query-reviewer flags. ✗ = don't, ✓ = do.
- ✗ `const user = await getUser(id); const posts = await getPosts(id)` in a server component ✓ `const [user, posts] = await Promise.all([getUser(id), getPosts(id)])`, or start both promises and stream the slower part inside `<Suspense>`.
- ✗ a layout/page awaits data, then a child server component awaits more data that didn't need it ✓ start every fetch at the top, in parallel, and pass data or promises down.
- Server components and route handlers that query the database directly follow prisma.md / mongoose.md / sql-raw.md.
- **The page is the data list:** the page's server component (or route segment) starts every fetch it needs at the top, together, and passes data or promises down; client components fetch only on a user action.
- ✗ client components fetching on mount what the server page could have loaded ✓ load it in the server component; use the client cache only for interactive data.
- ✗ dialogs, tabs or panels fetching while closed ✓ fetch when they open.
- Saves (server actions / route handlers) return the updated data so the client can update its cache instead of refetching everything; revalidate only the paths/tags the save changed.
