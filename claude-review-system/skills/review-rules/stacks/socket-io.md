# Stack: socket-io (real-time)

Detect: `socket.io` dependency.

## Discovery
- Server setup file, auth middleware on connection (`io.use`), room naming (`store_{id}`, `user_{id}`), and the helper functions used to emit (`notifyStore`, `notifyUser`…).

## Gap checks
- New emits use the recorded helpers, not raw `io.emit` / `getIO().to(...)`, where peers do.

## Security checks
- Connections are authenticated; joining a room checks the user belongs to that tenant/user/order.
- No global `io.emit` of tenant or user data.
- Incoming socket events validated like HTTP input.
