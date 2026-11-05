# Stack: payments-webhooks (Stripe, local gateways, WhatsApp/Meta, any inbound webhook)

Detect: `stripe` dependency, or routes/files named `*webhook*`, `*callback*`, `*ipn*`, `*payment*`.

## Discovery
- Every inbound webhook route, its provider and how it verifies the sender (signature header + raw body, shared secret, IP allow-list, verify token).
- Raw-body handling (Stripe needs the raw body before JSON parsing).
- Where payment status is changed and whether it is idempotent (event ID stored).

## Security checks
- Signature/secret verified before any state change; verification uses constant-time compare and the raw body.
- Idempotency: replayed events don't double-credit/double-ship.
- Amount, currency and order ID taken from the verified provider data or server records, never from client input or the redirect URL.
- Success redirect pages don't mark orders paid; only the verified webhook does.
- Webhook routes are on the public allow-list and nothing else is exposed with them.
