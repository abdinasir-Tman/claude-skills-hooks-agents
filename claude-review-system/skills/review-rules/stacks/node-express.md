# Stack: node-express (Express, Hono, Fastify, plain Node HTTP)

Detect: `express`, `hono`, `fastify` or `@nestjs/core` in a `package.json` that is not the frontend.

## Discovery
- Route registration: grep `router\.(get|post|put|patch|delete)`, `app\.(get|post|use)`, `new Hono`, `\.route\(`. Record the folder(s) and file naming (`*.routes.ts`, `routes/*.ts`) and the file that mounts them (often `app.ts` / `index.ts` / `server.ts`).
- Middleware chain: for every route, list the middleware between the path and the handler. Record the auth middleware name(s) and RBAC/guard names.
- Mount order: list `app.use` in order. Catch-all handlers (`/{*path}`, `*`, auth library handlers) shadow anything registered after them — record which ones exist.
- Validation library and where schemas live (`schemas/`, `validators/`, `dto/`), and how controllers call it (`.parse`, `.safeParse`, `validate(schema)` middleware).
- Error handling: the shared error middleware / `asyncHandler` wrapper, if any.
- Layering: routes → controllers → services → data? Record the real layer folders by opening 2–3 peers.
- Registration points a new endpoint needs (route index, OpenAPI/docs, permission seeder, frontend API client).
- Rate limiting / CORS / helmet config location.
- (data access) Middleware that attaches the current user/tenant to the request (handlers must reuse it, not reload it); the service functions that own each model.

## Gap checks
- New endpoint follows the peer layering (no DB calls in routes if peers use services).
- New route file is mounted where peers are mounted; route added to every registration point recorded in the rules.
- Errors go through the shared wrapper/middleware, not ad-hoc `res.status(500)` with swallowed errors.

## Security checks
- Every new route has the auth middleware unless it is on the public allow-list in `security-rules.md`.
- Every authenticated route has the guard/RBAC middleware the rules require.
- Body, query and params are validated before use; raw `req.body` / `req.query` / `req.params` never flow into DB `where`/`data`, file paths, shell commands, redirects or URLs fetched by the server (SSRF).
- Custom routes that must win are registered before any catch-all recorded in the rules.
- No user identity read from headers/body when the session is the source of truth.
- Redirect targets validated against an allow-list (open redirect).
- CORS: no `origin: true`/`*` together with `credentials: true`.
- Error responses don't return stack traces or internal messages in production.

## Data access
Patterns the writer follows (data-access skill) and the query-reviewer flags. ✗ = don't, ✓ = do.
- A controller calls one service function per need; a service doesn't chain other services' single-record lookups when one query (or one parallel group) answers it.
- ✗ `const a = await svcA(…); const b = await svcB(…)` where `b` doesn't use `a` ✓ `const [a, b] = await Promise.all([svcA(…), svcB(…)])`.
- ✗ re-loading the user/tenant that middleware already attached ✓ read it from the request.
- One endpoint per screen-sized need when the data is always shown together (see react-vite.md).
