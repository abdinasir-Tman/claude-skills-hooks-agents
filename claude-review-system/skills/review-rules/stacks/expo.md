# Stack: expo / react-native

Detect: `expo` or `react-native` dependency.

## Discovery
- Router (expo-router `app/` groups) and route groups per role.
- Token storage (`expo-secure-store` vs AsyncStorage) and API client.
- Deep link scheme (`app.json` `scheme`, linking config).
- i18n and theme setup; shared components with the web app if any.
- (data access) The API client and query hooks (shared with the web app or not); prefetch usage; where each screen declares its data; what the root layout loads on every screen.

## Gap checks
- New screen registered in the right route group/layout like peers; strings in every locale.
- Loading, empty and error states where peers have them.

## Security checks
- Tokens and secrets only in `expo-secure-store` (Keychain/Keystore), never AsyncStorage or plain files.
- No API keys/secrets in `app.json`/`app.config` `extra` or `EXPO_PUBLIC_*` that must stay secret.
- Deep-link params validated before navigation or API calls; no auth actions triggered by a link without confirmation.
- Role-gated screens are UX only — backend routes must enforce the same check.
- No `http://` API URLs in production config; no disabled TLS checks.

## Data access
Patterns the writer follows (data-access skill) and the query-reviewer flags. ✗ = don't, ✓ = do.
- Same rules as react-vite.md: a screen's requests start together from route params (`useLocalSearchParams`) and the session; no child fetch chains; one endpoint for data shown together; no `useEffect` fetching of server data.
- Mobile latency is higher, so every waterfall step costs more: prefetch the next screen's data on press when the data layer supports it.
- **The screen is the data list:** one screen-level hook (or loader) starts all of the screen's requests together; child components read from the cache.
- ✗ tabs, modals or background screens fetching while not focused ✓ fetch when the screen/tab is focused or the modal opens; pause polling while the app is in the background.
- The cache-refresh and wasted-request rules from react-vite.md apply unchanged (one key per resource, `setQueryData` from saves, exact-key invalidation, realtime update or invalidate).
