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

## What's implemented (headline items)
- Catalog + cascading Make/Model filter, body-type strip (8 MDI silhouettes)
- Auction calendar (server-side RU translation), internal mirror pages
- Vehicle detail with 3-stage EngagementPanel + urgency widget
- Price guidance ("Прогноз цены ухода" / "Ваш потолок ставки" / "Ориентир под ключ")
- Lead modal, live market strip, ending-soon carousel, deposit explainer
- AI chat "Татьяна" with admin-configurable persona + 6-step AI-подборщик quiz
- Hourly importers (Turners + Manheim NZ/AU + Pickles AU) — 1602 vehicles
- Daily auto-generated email campaigns (Mailchimp / Sendsay)
- Stripe Checkout for NZ$1,000 base deposit
- Russian customs + transport + RUB calculator (+3% platform margin)
- Admin: vehicles, leads (interests + offers), bids, deposits, sources, import,
  branding, calendar, invoices, logistics, CRM, clients, campaigns, settings
- TOTP-2FA admin login
- Saved Searches with APScheduler + Resend email + Telegram bot alerts
- Tiered deposits: NZ$1,000 → 20% (>$20k) → 30% (>$40k)

## Done in iter17 (27.06.2026) — today's work
- **P0 fix: "Ориентир под ключ"** — was showing FOB×fx-rate (~56k ₽ for expensive
  cars). Now uses `calculate_ru_landed_cost()` with vehicle-derived defaults so
  the tile includes RU customs + утильсбор + freight + insurance. New service
  helper `_estimate_ru_landed_for_vehicle()` in `services/auto_service.py`.
  Verified: Mercedes G63 @ $180k now shows «от 14 627 170 ₽» (was ~56k ₽).
- **AI estimate sanity rules** — new `sanitize_ai_estimate()` in
  `services/auto_intel_engine.py`. Clamps `estimate_low >= current_bid`, caps
  `estimate_high` at `max(cur×4, buy_now×1.1, low×1.6)`, keeps `recommended_max_bid`
  inside `[current×1.05, high]`. Adds `auction_stage` tag: `opening | active | peaking`.
  Applied in both `list_vehicles()` and `get_vehicle()` at read-time (no DB writes).
- **PriceGuidance UX** — labels renamed:
  «Оценка аукциона ИИ» → **«Прогноз цены ухода»** (with hint "ожидаемая финальная
  цена на торгах"); «Рекомендуемая ставка» → **«Ваш потолок ставки»** (hint
  "выше — переплата"); «Ориентир под ключ» hint = "всё включено: таможня РФ +
  доставка до Владивостока". New pill "Торги только открылись — финальная будет
  выше" surfaces when `auction_stage=opening`. Disclaimer rewritten so customers
  don't misread the AI forecast as "site wants 5× the current bid".
- **Payment terms softened**  — `FULL_PAYMENT_WINDOW_HOURS` moved from 24 → 72,
  new `FULL_PAYMENT_GRACE_HOURS=24`, `bullets_ru[3]` reworded to "штрафы с
  25-го часа + депозит удерживается после 72 часов". Version bumped to
  `v2026.06.27.1`.
- **PaymentTermsBanner** — dropped the harsh "Полная оплата — 24 часа / депозит
  удерживается" row from the vehicle page. Compact mode gets a one-liner link
  to `/auto/terms#terms-section-7`; full mode gets a footnote paragraph.
- **AutoTerms.jsx** — new section 7 «Сроки оплаты после выигрыша и штрафы» with
  softened three-paragraph wording (24 h standard, штрафы from hour 25, forfeit
  only after 72 h). Sections 8/9 shifted.
- **Quiz Save-Search CTA** — new `QuizSaveSearch.jsx` mounted at the end of the
  quiz result view. Neat, in-line-with-design panel (subtle blue tint, Bell
  micro-icon in existing `auto-btn`), maps quiz form → SavedSearchFilters
  (budget_nzd_max, first body_type, country, damage_only from repair="any").
- **Catalog sort fix** — first ~500 vehicles were price-less scrapes, so the
  default catalog was empty of numbers. Aggregation now sorts by `_has_price
  DESC, created_at DESC` — priced items always surface first.
- **Auth import fix** — pre-existing missing `AutoLogisticsStatus` import in
  `services/auto_service.py` (used in `_on_vehicle_won`).
- **CSS** — closed an unclosed `.auction-event__empty` block that had corrupted
  the payment-terms + admin-2FA rules; added `.payment-terms__link` +
  `.quiz-save*` styles.

## Backend tests
- `/app/backend/tests/test_iter18_landed_sanity_terms.py` (iter18) — 7/7 pass,
  0 critical. Verified: `landed_estimate` on `/vehicles/{id}`, sanity + stage
  on list, `/payment-terms` v2026.06.27.1 with 72h + softened bullets_ru[3],
  `/ru-customs/calc`, `/vehicles/{id}/landed-defaults`, `/quiz/meta+submit`.

## V2 backlog (post-MVP)
- 🟡 **P1** — Market Intelligence Engine Phase 2: Playwright/WebSocket capture
  for live Simulcast prices (currently only AI-estimated).
- 🟡 **P1** — Catalog is polluted by Pickles AU non-vehicle stock (portable
  buildings, steel barriers, crash-barrier road hardware). Add a scraper
  post-filter to drop rows whose `body_type/title` don't match car / motorbike
  / truck vocabularies. Cars (232 hatchbacks, 99 sedans) exist in DB but many
  lack `current_price_nzd` — investigate whether scraper should hoist
  `starting_price_nzd` into `current_price_nzd` at import time.
- 🟢 P2 — Виджет «Похожие проданы за NZ$X–Y» on the vehicle page (needs
  sold-price history).
- 🟢 P2 — Real scrapers for Motorbikes / Trucks / Heavy Machinery.
- 🟢 P2 — Continue extracting `routes/auto/{intel,sources,importers,payments,
  email,vehicles}.py` from the remaining 1700-line `auto_routes.py`.
- 🟢 P2 — Self-host branch hero photos in `/public/branding/` to remove Unsplash
  hot-link risk.
- 🟢 P2 — Resend domain verification for production.
- 🟢 P2 — Seed a couple of end-of-life listings so `/landed-defaults` parts
  scheme path can be regression-tested.
- 🟢 P2 — YooKassa / CloudPayments for Russian cards (Stripe test only).
- 🟢 P2 — Mobile / separate admin app.
- ⛔ P4 (declined) — Japanese auctions.

## Production launch checklist
1. Profile → Universal Key — balance for chat + email.
2. Admin → Settings — production Mailchimp / Sendsay keys.
3. Admin → Settings — switch Stripe to live mode (or migrate to YooKassa).
4. Add scraper category filter so non-vehicle Pickles stock is excluded.
5. End-to-end customer flow: register → deposit → bid → win → CRM order.
