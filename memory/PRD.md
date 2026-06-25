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

## Done in iter10–iter16 (25.06.2026)
- **Iter10–13** — RUB/NZD display, АИ-подборщик, Deep CRM timeline, refactor of auto_routes.py, Saved Searches (Resend email + Telegram bot), header overflow fix, Otahuhu image fix, Manheim NZ auctions in calendar.
- **Iter14** — Internal auction mirror (no more outbound redirects to Turners/Manheim). New page `/auto/auctions/event/:eventId`, endpoint `GET /api/auto/auctions/events/{event_id}`.
- **Iter15** — Bulk catalogue mirror. Expanded TurnersImporter (all 24 branches + damaged + trucks), Manheim paginates 50 pages × 3 search paths, Pickles paginates. New admin endpoint `POST /admin/sources/import-all` runs as a background task with `GET /admin/sources/import-status` polling. Catalogue grew **from 31 → 1608 vehicles** (832 Turners + 732 Manheim + 31 Pickles), cleaned 8 fake aggregator tiles.
- **Iter16** — Tiered payment-terms policy.
   - Base deposit NZ$1,000 (lots ≤ NZ$20,000)
   - 20% deposit (NZ$20,000 < lots ≤ NZ$40,000)
   - 30% deposit (lots > NZ$40,000)
   - Full payment within 24h of winning, otherwise deposit forfeited.
   - Service: `services/auto_payment_terms.py` (`required_deposit_nzd`, `payment_terms_summary`).
   - Endpoints: `GET /api/auto/payment-terms` (public), `GET /api/auto/vehicles/{id}/deposit-required`.
   - `place_bid()` enforces the per-vehicle deposit before accepting a bid (403 with required amount).
   - Component: `PaymentTermsBanner` (4 tier rows + per-vehicle highlight, with 1-hour localStorage cache).
   - Mounted on `/auto/vehicle/:id` between PriceGuidance and EngagementPanel.

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

