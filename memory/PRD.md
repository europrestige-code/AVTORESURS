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
  «Оценка аукциона ИИ» → **«Прогноз цены ухода»**; «Рекомендуемая ставка» →
  **«Ваш потолок ставки»**; «Ориентир под ключ» hint = "всё включено: таможня РФ
  + доставка до Владивостока". New pill "Торги только открылись — финальная
  будет выше" appears when `auction_stage=opening`. Disclaimer rewritten so
  customers don't misread the AI forecast as "site wants 5× the current bid".
- **Payment terms softened** — `FULL_PAYMENT_WINDOW_HOURS` moved from 24 → 72,
  new `FULL_PAYMENT_GRACE_HOURS=24`. Version bumped to `v2026.06.27.1`.
- **PaymentTermsBanner** — dropped the harsh "Полная оплата — 24 часа" row from
  the vehicle page. Compact mode gets a one-liner link to `/auto/terms#terms-section-7`.
- **AutoTerms.jsx** — new section 7 «Сроки оплаты после выигрыша и штрафы»
  (24 h standard, штрафы from hour 25, forfeit only after 72 h).
- **Quiz Save-Search CTA** — new `QuizSaveSearch.jsx` at end of quiz result.
  Maps quiz form → SavedSearchFilters, Bell icon in existing `auto-btn` style.
- **Catalog sort fix** — aggregation now sorts by `_has_price DESC, created_at DESC`.
- **Backend tests iter18** — 7/7 pass.

## Done in iter19 (27.06.2026) — follow-up work
- **Catalog clean-up** — new `is_non_vehicle()` predicate in
  `services/auto_source_importers.py` drops Manheim `/trucks-machinery/`
  category rows (barriers, portable buildings, cement mixers, tree diggers,
  concrete blocks, portable toilets). Wired into `ImportOrchestrator.run_one()`
  so future imports skip them, and exposed as
  `POST /api/auto/admin/sources/cleanup-non-vehicles` for one-shot DB sweeps.
  First sweep deleted **155 rows** — catalog went 1603 → 1448 real vehicles.
- **Manheim price fallback** — extended `_parse_search()` with four regex
  fallbacks (Current Bid / Reserve Price / Buy Now / bare `$X,XXX`) so cards
  that don't literally say "Starting Bid" still get `current_price_nzd`
  populated. Bounded to $100–$3M to filter out lot numbers / phone digits.
- **Sold-history widget** — new `services/auto_sold_history.py` +
  `GET /api/auto/vehicles/{id}/sold-history` endpoint. Prefers real
  `auction_observations` (sold=true, same make/model, year±N). Falls back to
  live catalog prices with a `source: 'current_listings'` flag so the frontend
  can label «Похожие выставлены за» vs «Похожие проданы за». New tile
  `components/auto/SoldHistory.jsx` mounted between PriceGuidance and
  PaymentTermsBanner. Auto-hides on `source: 'insufficient'`.
- **Deposit uploads on Mongo** — refactored `POST /deposit/upload` and
  `GET /deposit/{id}/proof` to store receipt bytes in a new
  `auto_deposit_proofs` collection instead of the pod-local disk (ephemeral
  in production).
- **Backend tests iter19** — 13/13 pass. Minor items flagged: catalog `limit>100`
  silently returns [] (clamp or 422), URL blacklist may drop legit
  light-commercial vans, sold-history needs seed observations for the
  `sold_observations` branch regression.

## Done in iter20 (27.06.2026) — van whitelist
- **Van/Utility whitelist** — `is_non_vehicle()` now runs title checks
  BEFORE the URL check, so legit light-commercial vans and utility trucks
  parked under Manheim's `/trucks-machinery/` URL don't get swept:
  Hiace, Transit, Sprinter, Vito, Crafter, Ducato, Master, Trafic,
  Hilux, Ranger, Navara, Amarok, BT-50, Colorado, D-Max, Tacoma, F-150,
  Amarok, Patrol, Pajero, Wrangler and more. Hard-blacklist words (portable
  building, steel barrier, cement mixer, trailer chassis, …) still win.
- **Backend tests iter20** — 14/14 pass, 0 critical.

## Done in iter21 (27.06.2026) — hammer-price capture
- **`services/auto_hammer_capture.py`** — two-phase pipeline for real sold
  data:
  - `snapshot_current_listings()` writes an `official_listing` observation
    for every priced live lot (deduped per {source, lot_ref, price} within
    24 h). Feeds the AI estimator with broader base while sold data
    accumulates. Snapshot pass populated **200 observations** immediately.
  - `sweep_stale_as_sold()` — lots not re-scraped in the last 48 h AND
    actively-touched within the last 5 days become `sold=True`,
    `source_type='public_archive'` observations. Their `status` also
    flips to `sold`. The 5-day active-window guard prevents mass false
    positives from initial-batch imports whose rows never get re-touched.
- **Scheduler** — new `_hammer_loop` in `auto_scheduler.py` runs every 6 h,
  interleaves snapshot + sweep, and reports via `status()`.
- **Admin endpoint** `POST /api/auto/admin/sources/capture-hammer?stale_hours=N`
  triggers both phases manually.
- **Backend tests iter21** — 12/12 pass, 0 critical.

## Done in iter22 (27.06.2026) — scraper autoloop + van chip
- **Scraper autoloop** — new `_scraper_loop` in `auto_scheduler.py`.
  Runs `ImportOrchestrator.run_all(limit_per_source=50)` every hour after a
  90 s initial delay so the catalog auto-refreshes without an admin poke.
  Per-source failures stay isolated. `status()['scraper_autoloop']` shows
  the last run's per-source `{fetched, created, updated, skipped, failed}`.
- **Van & Pickup preset chip** — new `PRESET_FILTERS` dict in
  `auto_routes.py` + `GET /preset-counts` endpoint. The `van_pickup` regex
  covers 60+ vans and utility models (Hiace, Transit, Sprinter, Vito,
  Crafter, Ducato, Master, Hilux, Ranger, Navara, Amarok, BT-50,
  Colorado, D-Max, Tacoma, F-150 …). New `PresetChips.jsx` renders a
  pill "Фургоны и пикапы (267)" under `BodyTypeStrip` on `/auto` and
  `/auto/catalog`. Clicking applies the regex via the existing catalog
  `search` filter — jumps straight to 267 vehicles.
- **Backend tests iter22** — 8/8 pass, 0 critical.

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
