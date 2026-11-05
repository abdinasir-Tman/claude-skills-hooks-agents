# Stack: better-auth (auth library)

Detect: `better-auth` dependency.

## Discovery
- Auth config file (`auth.ts`), plugins enabled (admin, organization, sso, twoFactor, jwt…), `databaseHooks`.
- Where the handler is mounted (`toNodeHandler(auth)` / `auth.handler`) and the path pattern; which custom `/api/auth/*` routes exist and whether they are mounted before it.
- How backend middleware reads the session (`auth.api.getSession({ headers })`) and attaches the user.
- Cookie settings (`secure`, `sameSite`, cross-subdomain), `trustedOrigins`.
- Any auto-promotion / role assignment hooks.

## Security checks
- Custom auth routes registered before the catch-all handler (otherwise shadowed).
- Changes to `databaseHooks`, role assignment, email-domain rules, `trustedOrigins` or cookie flags are flagged HIGH for human review.
- Session is read from the auth library, never from a client header/body user ID.
- Admin plugin endpoints (impersonate, ban, set-role) guarded and audited.
- `BETTER_AUTH_SECRET` never logged; `secure` cookies in production.
