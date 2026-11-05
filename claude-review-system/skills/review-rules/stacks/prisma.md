# Stack: prisma

Detect: `prisma` / `@prisma/client` dependency, `schema.prisma` file.

## Discovery
- Tenancy: in `schema.prisma`, find columns like `storeId|orgId|organizationId|tenantId|companyId|restaurantId|propertyId|clinicId|workspaceId|accountId`. A column on ≥3 models with a matching middleware/helper that resolves it per request → MULTI-tenant candidate. List the tenant-owned models.
- Tenant source: grep for the helper/middleware that resolves the tenant (`req.tenantId`, `getStoreId`, `getOrgId`, Prisma client extensions / `$extends` that inject the filter). Record whether scoping is automatic (extension) or manual (every query).
- Ownership: models with `userId`/`ownerId`/`createdById` — record them for IDOR checks.
- Soft delete (`deletedAt`) and whether queries must exclude it.
- Raw SQL use: grep `\$queryRaw`, `\$executeRaw`, `Unsafe`.
- Migrations folder and how new migrations are made (`prisma migrate dev` vs hand-written SQL); seeders (permissions, roles).
- Shared `select` objects for safe user fields (to avoid leaking `passwordHash`).
- (data access) Shared `select`/`include` objects and where-builders (path:symbol); whether the `relationJoins` preview feature is enabled in `generator client`; how the query log is switched on locally (PrismaClient `log` option / env flag in the client file); any test helper that counts queries.

## Gap checks
- Schema change has a migration; new enum values / permissions are in the seeder if peers are.

## Security checks
- Every query on a tenant-owned model filters the tenant column (unless an extension does it — then check the extension is not bypassed with a bare client).
- `findUnique`/`update`/`delete` by `id` on a tenant/owned model also checks tenant/owner (`findFirst({ where: { id, storeId } })` or a check after load).
- Client-supplied tenant IDs are validated against the resolved tenant.
- No `$queryRawUnsafe` / `$executeRawUnsafe` with user input; tagged `$queryRaw` only.
- No mass assignment: `data: req.body` or spreading unvalidated input into `create`/`update` (role, tenant, price, isAdmin fields).
- Responses don't return full `User` (passwordHash, tokens) or other tenants' rows.

## Data access
Patterns the writer follows (data-access skill) and the query-reviewer flags. ✗ = don't, ✓ = do.
- ✗ `const user = await prisma.user.findUnique({ where: { id } }); const posts = await prisma.post.findMany({ where: { userId: user.id } })`
  ✓ `prisma.user.findUnique({ where: { id }, select: { id: true, name: true, posts: { select: {…}, orderBy: { createdAt: 'desc' }, take: 20 } } })` — or, when they are separate parts of the response, `Promise.all([prisma.user.findUnique({ where: { id } }), prisma.post.findMany({ where: { userId: id } })])`.
- ✗ `const post = await prisma.post.findUnique({ where: { id } }); const author = await prisma.user.findUnique({ where: { id: post.authorId } })`
  ✓ `prisma.post.findUnique({ where: { id }, include: { author: { select: { id: true, name: true, avatar: true } } } })`
- ✗ `for (const p of posts) p.author = await prisma.user.findUnique(…)` — and `await Promise.all(posts.map(p => prisma.user.findUnique(…)))`, which is still one query per row
  ✓ `include: { author: { select: … } }` in the list query, or one `findMany({ where: { id: { in: ids } } })` + a `Map`.
- ✗ `const store = await prisma.store.findFirst({ where: { id: storeId, ownerId } }); if (!store) …; const orders = await prisma.order.findMany({ where: { storeId } })`
  ✓ `prisma.order.findMany({ where: { storeId, store: { ownerId } } })` — relation filters: `some`/`every`/`none` for to-many, `is`/`isNot` for to-one. When "not found" and "forbidden" must give different answers, run the two queries in parallel instead.
- ✗ `const items = await prisma.x.findMany(…); const total = await prisma.x.count(…)`
  ✓ `const [items, total] = await prisma.$transaction([prisma.x.findMany(…), prisma.x.count(…)])` or `Promise.all`; per-row counts with `_count: { select: { posts: true } }`; totals with `aggregate` / `groupBy` — never load rows to count them in JS.
- ✗ `for (const i of items) await prisma.orderItem.create({ data: i })`
  ✓ `createMany` / `createManyAndReturn` (PostgreSQL), a nested `create` inside the parent's `create`, or one `$transaction`.
- ✗ `findUnique` → check `storeId` in JS → `update`
  ✓ `updateMany({ where: { id, storeId }, data })` and check `count`, or `update({ where: { id, storeId }, data })` (non-unique filters are allowed next to the unique field) and handle `P2025`.
- ✗ `include: { posts: true }` on a list (every column, unbounded) ✓ `select` the fields used + `take` on to-many relations; `omit` for big or secret columns.
- ✗ re-loading the current user/tenant in the handler ✓ use what the auth/tenant middleware put on the request.
- Without the `relationJoins` preview, Prisma runs one statement per relation level for `include`/relation `select` — constant, not N+1. Count it in the plan's Statements column.
- Schema: every relation declared with `@relation`; FK fields used in `where`/`orderBy` have `@@index` (PostgreSQL doesn't index foreign keys automatically).
