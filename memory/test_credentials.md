## Admin
- Email: admin@buyanywhere.com
- Password: admin12345
- Role: admin

## Verified customer (deposit already confirmed)
- Email: client@buyanywhere.com
- Password: client12345
- Role: customer
- Auto deposit: VERIFIED (can place bids immediately)

## Customer without deposit (used to verify deposit gate)
- Email: client2@buyanywhere.com
- Password: client12345
- Role: customer
- Auto deposit: none

## Notes
- Auth endpoint: POST `${REACT_APP_BACKEND_URL}/api/auth/login` with `{ email, password }` returns `access_token`.
- BuyAnywhere admin panel still uses the legacy hardcoded admin (`/api/admin/auth/login` / any password).
- Auto admin endpoints (`/api/auto/admin/...`) use the standard customer JWT and require `users.role == "admin"`.
- The chat widget has a new "Подобрать авто за 60 секунд" CTA that opens a 5-step AI quiz. No login required.
- Admin → Клиенты tab now lists registered users + anonymous leads with activity counts and a click-to-open CRM timeline drawer.
