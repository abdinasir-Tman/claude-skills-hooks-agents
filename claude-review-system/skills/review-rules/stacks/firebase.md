# Stack: firebase (Functions, Firestore, Storage, Auth)

Detect: `firebase-functions`, `firebase-admin`, `firebase.json`, `firestore.rules`, `storage.rules`.

## Discovery
- Functions entry file and how functions are exported (`onRequest`, `onCall`, triggers); region/runtime config.
- `firestore.rules` / `storage.rules` locations and the helper functions they define (isSignedIn, isOwner, hasRole).
- Custom claims / role model; where claims are set.
- Collections that are tenant/owner scoped (fields like `ownerId`, `restaurantId`).
- Emulator setup for local testing.
- (data access) Fields denormalized onto documents for lists; batch-read helpers (`getAll`); `count()` usage.

## Gap checks
- New function exported from the entry file like peers; rules updated when a new collection/path is added.
- Indexes added to `firestore.indexes.json` for new compound queries.

## Security checks
- `onCall`: checks `request.auth` (or `context.auth`) and roles; `onRequest`: verifies an ID token or signature — HTTP functions are public by default.
- Admin SDK bypasses rules: every admin read/write in a function enforces the owner/tenant/role check itself.
- Rules: no `allow read, write: if true` / `if request.auth != null` on data that needs owner/role checks; writes validate fields (no client-set `role`, `price`, `ownerId`).
- Storage rules limit size and content type; paths include the owner.
- Secrets via `defineSecret` / config, not in code.

## Data access
Patterns the writer follows (data-access skill) and the query-reviewer flags. ✗ = don't, ✓ = do.
- Firestore has no joins. Data that a list always shows (author name, avatar) is denormalized onto the document, or fetched once for the whole page with `getAll(...refs)` (Admin SDK) or `in` queries on ids in chunks within the SDK's limit — never `get()` per row.
- ✗ `await` one `doc.get()` after another for independent docs ✓ `Promise.all` or `getAll`.
- ✗ reading a whole collection to count it ✓ the `count()` aggregation (`query.count().get()` in the Admin SDK, `getCountFromServer` in the web SDK).
- Every read is billed: an N+1 here costs money as well as time.
- Lists use `limit()` + a cursor (`startAfter`); compound queries have their index in `firestore.indexes.json`.
