# BuyAnywhere Auto / АвтоРесурс — PRD

## Original problem statement
Russian-language vehicle sourcing + proxy-bidding platform for NZ & AU auctions
(Turners, Manheim, Pickles). Customer-facing in RU, prices in RUB, hourly auto
import, AI translation/chat, automated email marketing, dark premium UI.

## Product personas
1. **Visitor** — browses anonymously, can express interest / request quote.
2. **Registered customer (no deposit)** — can save, ask, propose price.
3. **Verified customer (deposit ✓)** — can submit official bids.
4. **Admin** — runs inventory, leads, settings, campaigns, CRM.

## Three-stage engagement flow (implemented 25.06.2026)
1. **Interest**  → soft lead (anyone). Posts `/api/auto/interests`.
2. **Offer**    → "Предложение цены" (authed, no deposit). Posts `/api/auto/offers`.
3. **Bid**      → "Ставка" (authed + deposit verified). Posts `/api/auto/vehicles/{id}/bid`.
   Server enforces `deposit_status=verified` → 403 otherwise.

Critical legal distinction:
- **Предложение цены** = non-binding indication.
- **Ставка** = binding instruction.
The DB stores them in separate collections (`auto_offers` vs `auto_bids`).

## What's implemented (as of 25.06.2026)
- Catalog + cascading Make/Model filter
- Body-type strip (8 MDI silhouettes — Sedan/SUV/Wagon/Hatch/Coupe/Conv/Van/Utility)
- Auction calendar (server-side RU translation of title/branch/city)
- Blue MapPin tags everywhere city names appear
- Vehicle detail with **3-stage EngagementPanel** (visitor / no-deposit / verified)
- Urgency widget (countdown + watchers + interested + offers)
- Price guidance (Оценка от / Рекомендуемая ставка / Ориентир под ключ)
- Lead modal (name + phone + city + budget + message) → silent CRM contact mirror
- Live market strip on homepage (6 real DB counts)
- Ending-soon carousel (72h window)
- Deposit explainer block (safe / refundable / countable)
- Per-branch auction photo + Damaged + EOL branded photos
- AI chat "Татьяна" with admin-configurable persona
- Hourly importers (Turners + Manheim NZ/AU + Pickles AU)
- Daily auto-generated email campaigns (admin can choose Mailchimp / Sendsay)
- Stripe Checkout for NZ$1,000 deposit
- Russian customs + transport + RUB calculator (+3 % platform margin)
- Admin: vehicles, **leads (interests + offers)**, bids, deposits, sources,
  import, branding, calendar, invoices, logistics, CRM, clients, campaigns, settings

## V2 backlog (post-MVP — superseded by the iter10–iter13 list above)
- (see «Done in iter10–iter13» section for completed P1 items)

## Done in iter10–iter13 (25.06.2026)
- **RUB primary / NZD secondary** price display across `PriceGuidance.jsx` and `VehicleCard.jsx`.
- **АИ-подборщик** — 6-step quiz inside the Татьяна chat widget (added repair + buyer-type steps). Quiz is now the DEFAULT mode when the chat opens — Tatiana sells first, answers questions second (link «Просто задать вопрос →»).
- **Deep CRM timeline** — Admin → Клиенты merges users + leads with activity counts and a chronological event drawer (6 event types).
- **auto_routes.py refactor** — chat/quiz, engagement, admin-CRM and saved-searches extracted to `routes/auto/{chat_quiz, engagement, admin_crm, saved_search, _deps}.py`.
- **Saved Searches** — `services/auto_saved_search_service.py` + `routes/auto/saved_search.py`. `POST /saved-searches`, `GET /saved-searches`, `DELETE`, `PATCH /toggle`, `POST /saved-searches/preview` (public). Scheduler runs every 15 min via `_saved_search_loop`. Notifications go through `services/auto_notify_service.py`:
   - **Resend** transactional email (env `RESEND_API_KEY`, `SENDER_EMAIL`).
   - **Telegram bot** (env `TELEGRAM_BOT_TOKEN`, username `AvtoresursAlertsBot`). Binding flow: `POST /telegram/start-binding` → user opens deep-link → `POST /telegram/webhook` receives `/start link_<token>` and attaches chat_id.
   - New page `/auto/my/searches` with Telegram-binding UI and saved-search list.
   - «Сохранить поиск» CTA next to the catalog filters.
- **Header overflow fix** (iter13) — «Календарь аукционов» → «Календарь», «Зарегистрироваться» → «Регистрация», max-w-[1600px], compact buttons. Verified 1280/1366/1440/1920.
- **Otahuhu image fix** (iter13) — replaced 404 Unsplash photo, hardened onError fallback chain → rotation → local placeholder.
- **Manheim NZ in auctions calendar** (iter13) — new `parse_manheim_page` + `fetch_manheim_auctions`. `refresh()` now returns `by_source={turners,manheim}`. 10 Manheim events surface alongside Turners on the homepage and `/auto/auctions`.

## V2 backlog (post-MVP)
- 🟡 P1 — Market Intelligence Engine **Phase 2**: Playwright/WebSocket capture for live Simulcast prices (currently AI-estimated)
- 🟢 P2 — Виджет «Похожие проданы за NZ$X–Y» on the vehicle page (needs sold-price history)
- 🟢 P2 — 2FA admin login
- 🟢 P2 — Real scrapers for Motorbikes / Trucks / Heavy Machinery verticals (UI + routes already wired)
- 🟢 P2 — Continue extracting `routes/auto/{intel,sources,importers,payments,email,vehicles}.py` from the remaining 1700-line `auto_routes.py`
- 🟢 P2 — Self-host branch hero photos in `/public/branding/` to remove Unsplash hot-link risk
- 🟢 P2 — Resend domain verification for production (currently only `europrestige@gmail.com` receives in test mode)
- 🟢 P2 — Quiz → auto-create a Saved Search from the user's answers
- 🟢 P2 — Mobile / separate admin app
- ⛔ P4 (declined) — Japanese auctions

## Production launch checklist
1. Profile → Universal Key — ensure balance for chat + email
2. Admin → Settings — drop production Mailchimp / Sendsay keys
3. Admin → Settings — switch Stripe to live mode
4. End-to-end customer flow: register → deposit → bid → win → CRM order

