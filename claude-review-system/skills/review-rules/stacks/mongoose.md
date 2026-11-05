# Stack: mongoose / MongoDB

Detect: `mongoose` or `mongodb` dependency.

## Discovery
- Models folder; tenant/owner fields on schemas (same names as prisma.md tenancy list); plugins that add tenant scoping automatically.
- Whether `strictQuery` / `sanitizeFilter` is set; any sanitizer middleware (`express-mongo-sanitize`).
- How IDs are validated (`isValidObjectId`, zod).
- (data access) Virtual populates defined on schemas; `.lean()` convention for reads; the `mongoose.set('debug', …)` switch; indexes declared on refs and filter fields.

## Gap checks
- New schema follows peer model files (timestamps, indexes, plugin use).

## Security checks
- NoSQL injection: no request objects passed straight into `find`/`findOne`/`updateOne` filters (`{ email: req.body.email }` where the body could be `{ "$ne": null }`); inputs validated as primitives or `sanitizeFilter` enabled.
- No `$where` or `mapReduce` with user input.
- Tenant/owner filter on every query of tenant/owned collections; `findById` followed by an ownership check.
- No `Model.create(req.body)` / `findByIdAndUpdate(id, req.body)` mass assignment.
- `select('-password')` or equivalent on user reads that leave the server.

## Data access
Patterns the writer follows (data-access skill) and the query-reviewer flags. ✗ = don't, ✓ = do.
- ✗ `const user = await User.findById(id); const posts = await Post.find({ user: user._id })`
  ✓ `const [user, posts] = await Promise.all([User.findById(id).select('name avatar').lean(), Post.find({ user: id }).sort({ createdAt: -1 }).limit(20).lean()])`, or a virtual populate on User.
- ✗ `const post = await Post.findById(id); const author = await User.findById(post.author)`
  ✓ `Post.findById(id).populate('author', 'name avatar').lean()`
- ✗ `findById` per row in a loop or `map` ✓ `populate` on the list (one extra query per path, batched with `$in`), or one `find({ _id: { $in: ids } })` + a `Map`; `$lookup` when you filter or sort by the joined data.
- ✗ `find()` then `countDocuments()` sequentially ✓ `Promise.all([find…, countDocuments…])`, or `$facet` in one aggregation.
- ✗ `for (…) await Model.create(x)` / `save()` in a loop ✓ `insertMany`, `bulkWrite`.
- ✗ `findById` → check the owner in JS → `save()` ✓ `findOneAndUpdate({ _id: id, owner: me }, update)` / `updateOne` with the scope in the filter.
- Read paths use `.lean()` and `.select()`; lists have `.limit()`; refs and filter/sort fields have indexes (`schema.index(...)`).
