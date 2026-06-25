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

## V2 backlog (post-MVP)
- Migrate 36 hex literals to `--ar-*` CSS tokens
- Motorbikes vertical (Turners + Manheim) — UI/routes ready; data pipeline pending
- Спецтехника vertical — UI/routes ready; data pipeline pending
- Refunds endpoint for unsuccessful bids (done — `/api/auto/admin/deposits/{id}/refund`)
- 2FA admin login
- "Похожие проданы за NZ$X-Y" block (needs sold-price history)
- Phase 4 (Japanese auctions) — declined by user
- Mobile / separate admin app

## Done in iter10–iter11 (25.06.2026)
- **RUB primary / NZD secondary** price display across `PriceGuidance.jsx` (two-line layout) and `VehicleCard.jsx` (RUB main, NZD muted subtitle).
- **АИ-подборщик** — 5-step quiz inside the Татьяна chat widget. CTA `Подобрать авто за 60 секунд`. Posts to `/api/auto/quiz/submit`, persists to `auto_quiz_leads`, mirrors into `auto_interests (source='quiz')`, returns ranked matches (`AutoQuizService._match`).
- **Deep CRM timeline** — `routes/auto/admin_crm.py` + `services/auto_crm_timeline.py`. Admin → Клиенты merges registered users + anonymous leads with `interests/offers/bids/chat_messages/quiz_leads` counts, `last_activity`, `total_events`. Click row → drawer shows a merged chronological timeline of all six event types with coloured pills.
- **auto_routes.py refactor** — extracted chat/quiz, engagement, admin-CRM endpoints into `routes/auto/{chat_quiz, engagement, admin_crm, _deps}.py`. Aggregated via `router.include_router` at the bottom of `auto_routes.py`. 26/26 pytest GREEN (iter10 + iter11).

## Still pending refactor
- Peel out `routes/auto/{intel, sources, importers, payments, email, vehicles}.py` so `auto_routes.py` (~1700 lines) keeps shrinking.
- Add `routes/auto/__init__.py` aggregator or delete `routes/auto/_deps.py` import duplication once additional sub-routers are extracted.

## Production launch checklist
1. Profile → Universal Key — ensure balance for chat + email
2. Admin → Settings — drop production Mailchimp / Sendsay keys
3. Admin → Settings — switch Stripe to live mode
4. End-to-end customer flow: register → deposit → bid → win → CRM order

