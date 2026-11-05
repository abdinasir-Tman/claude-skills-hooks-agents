# Stack: react-vite (React SPA)

Detect: `react` + `vite` in a frontend `package.json`.

## Discovery
- Path aliases (`vite.config` / `tsconfig` `paths`) — record them.
- Data fetching layer (RTK Query `baseApi`, TanStack Query, axios client) and where endpoints are declared.
- Routing (react-router config file), nav/menu configs, i18n setup and locale files.
- Component folders (`components/ui`, feature folders) and the design-system components peers use.
- State management (Redux slices, Zustand stores).
- (data access) The base API file and how endpoints are injected (RTK Query) or the query-key / hook conventions (TanStack Query); query client defaults (`staleTime`, `refetchOnWindowFocus`, `retry`); which routes declare their data (loaders / prefetch) and the best one to copy, and which don't yet; what the shell/layout components fetch on every page; realtime → cache handlers (update vs invalidate); cache tag conventions.

## Gap checks
- Imports use the aliases, not deep relative paths, where peers do.
- New page registered in the router and nav config like peers; new strings added to every locale file.
- Loading, empty and error states exist where peers have them.
- Existing UI components reused instead of new near-copies.

## Security checks
- No auth tokens in `localStorage`/`sessionStorage` if the repo uses cookies (or per rules).
- No `dangerouslySetInnerHTML` with unsanitized data; no `eval`/`new Function`.
- No secrets in `VITE_*` env vars (they ship to the browser).
- Client-side permission checks are only UX — the matching backend route must enforce them (cross-check the route).
- External links with `target="_blank"` have `rel="noopener noreferrer"`; user-provided URLs are not put in `href` without a scheme check (`javascript:`).

## Data access
Patterns the writer follows (data-access skill) and the query-reviewer flags. ✗ = don't, ✓ = do.
- ✗ `const { data: user } = useGetUserQuery(id); const { data: posts } = useGetPostsQuery(user?.id ?? skipToken)` — waits for the user although `id` is in the route
  ✓ both hooks take the route `id` and run together; or one `GET /users/:id/profile` endpoint when they are always shown together.
- ✗ `<PostDetail>` loads the post, then `<AuthorCard authorId={post.authorId}>` fetches the author ✓ the post endpoint includes the author fields the card shows.
- ✗ `useEffect(() => { axios.get(…).then(setX) }, [])` for server data ✓ the repo's data layer (RTK Query endpoints injected into the base API, or TanStack Query hooks).
- ✗ list rows that each call a query hook (N requests) ✓ the list endpoint returns what the rows show; one batch endpoint for extras.
- ✗ the fetch starts only after a lazy route chunk renders ✓ start it from the route: a react-router data-router `loader`, a TanStack Router `loader` with the query client (see the loader bullet), or RTK Query `usePrefetch` / `api.util.prefetch` on hover or before navigating.
- `skip` / `skipToken` / `enabled: false` only when the input really comes from another response — and the Data loading plan says why.
- **The route is the page's data list.** TanStack Router + TanStack Query: `loader: ({ context, deps }) => { void queryClient.query(aQuery(ws)).catch(() => {}); void queryClient.query(bQuery(ws, deps.id)).catch(() => {}) }` with `loaderDeps: ({ search }) => ({ … })` for search params; `await queryClient.query({ ...opts, staleTime: 'static' })` only when a later request needs its value; `queryClient.infiniteQuery(opts)` for lists. In TanStack Query 5.104 `prefetchQuery` / `ensureQueryData` / `fetchQuery` / `prefetchInfiniteQuery` are deprecated (removed in the next major); older v5 versions only have those — check the installed types. react-router (data router): the route `loader` prefetches into the query client, or dispatches RTK Query `api.util.prefetch(...)`. Components then read the same query definitions (cache hit).
- ✗ several `useSuspenseQuery` calls in one component — each suspends before the next starts, so they run one after another ✓ `useSuspenseQueries`, or prefetch them all in the loader.
- ✗ a dialog, drawer, collapsed panel or hidden tab whose content mounts and fetches while closed ✓ `enabled: open`, or mount the content only when it opens.
- ✗ shell/layout components that poll a heavy list on every page to read one field (`memberId`, a count) ✓ a small endpoint or a field on data the shell already has; `select` to subscribe to one field; poll only on screens that show the status.
- ✗ the same resource under two keys, or a direct `fetch` beside the cache ✓ one `queryOptions` factory per resource in the feature's queries file, reused everywhere.
- ✗ `refetchInterval` on an infinite query — it re-sends every loaded page, one after another ✓ poll only the first page (`refetchInterval: (q) => ((q.state.data?.pages.length ?? 1) > 1 ? false : ms)`) or reset to page 1 first.
- ✗ `invalidateQueries()` without a key, or a broad prefix, after a save ✓ `setQueryData` from the save's response + invalidate only the exact keys it changed.
- ✗ a realtime event that writes the cache *and* invalidates the same queries; a second trigger for the same change (the mutation's `onSuccess` plus the event) ✓ one path; debounce bursts.
- ✗ `staleTime: 0` plus refetch on mount / window focus for data that realtime keeps current ✓ a `staleTime` per resource; `refetchOnWindowFocus: false` on realtime-kept queries.
- ✗ a whole list (members, staff, plans) loaded to turn ids into names ✓ the endpoint returns the names.
- ✗ `useEffect` that refetches/invalidates after a user action, or copies query data into state ✓ do it in the event handler or the mutation's `onSuccess`; derive values during render.
- ✗ a request per keystroke ✓ debounce the input (250–300 ms) before it becomes part of the query key.
