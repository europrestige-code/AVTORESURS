# BuyAnywhere Auto — PRD

## Original problem statement (Jan 2026)
Add a new vertical `BuyAnywhere Auto` to the existing BuyAnywhere platform: a
Russian-language vehicle sourcing and **internal proxy-bidding** platform for
New Zealand vehicles, plus inquiry-only Australia listings. Reuse existing
FastAPI + React + MongoDB + JWT auth. No new databases or auth systems.

## Architecture
- Backend (FastAPI on :8001) — new router `/api/auto` (in
  `backend/routes/auto_routes.py`) wired into existing `server.py`.
- Services:
  - `auto_service.py` — pricing formula, bid/deposit rules, indexes.
  - `auto_ai_service.py` — Emergent Universal Key + emergentintegrations
    (GPT-5.2; fallback gpt-4o-mini) — extraction, RU translation, risk summary.
  - `auto_import_service.py` — text / URL / CSV importer (URL fetch via httpx;
    falls back to Russian instruction message on failure).
- Mongo collections (with indexes): `auto_vehicles`, `auto_bids`,
  `auto_deposits`, `auto_inquiries`, `auto_invoices`, `auto_logistics_events`,
  `auto_watchlist`.
- Frontend (React on :3000): new routes at `/auto` (layout) with sub-routes
  index / catalog / vehicle/:id / dashboard / admin / how-it-works / fees /
  australia. Dark premium theme scoped under `.auto-root`.
- Auth: same JWT as the rest of BuyAnywhere (stored as `access_token`).
- Stripe (TEST key from env) for deposit Checkout Session, plus manual
  proof-upload + admin verify workflow.

## Core business rules implemented
- Deposit NZ$1,000 required to bid; status none / pending / verified / rejected.
- Bidding allowed only on country=NZ and listing_type=auction with
  status=available.
- New bid must be strictly higher than current active highest; equal bid is
  rejected with the exact spec message ("Такая ставка уже существует. Укажите
  сумму выше текущей максимальной ставки.").
- Previous active bids on a vehicle are marked `outbid` automatically.
- Australia listings are inquiry-only (no bids).
- Pricing formula: vehicle + 20% commission + transport (500) + forklift (0)
  + storage_days × 50 + documentation (250) + container share (3333) +
  optional FX-to-RUB.

## What's been implemented (2026-01)
- ✅ All backend models, services, routes per spec.
- ✅ Internal proxy bidding with deposit gate and outbid handling.
- ✅ Manual deposit upload + admin verify/reject; Stripe deposit checkout
  with auto-verify on `paid`.
- ✅ Watchlist / inquiries / invoices / logistics events.
- ✅ AI extraction from text, AI RU translation, AI risk summary
  (graceful fallback when AI fails or data is missing).
- ✅ Importer from text / URL / CSV (URL fetch + BeautifulSoup, falls back to
  Russian instruction message).
- ✅ React pages: AutoHome (hero + featured grid + how-it-works), AutoCatalog
  (filters + pagination + empty state), AutoVehicleDetail (gallery + bid
  panel + inquiry + price breakdown + watchlist), AutoDashboard (deposit +
  bids + invoices + logistics + watchlist + inquiries), AutoAdmin (vehicles
  CRUD, deposits verify/reject, AI translate/summary, import, invoices,
  logistics, clients), AutoHowItWorks, AutoFees (live calculator),
  AutoAustralia.
- ✅ `Авто` nav link in the main BuyAnywhere header.
- ✅ Seed script `python /app/backend/seed_auto.py` — 1 admin + 2 customers +
  12 vehicles (9 NZ + 3 AU).
- ✅ Backend tests in `/app/backend/tests/test_auto_backend.py`
  (35/36 pass; the one false failure is pytest-xdist test ordering).

## Test credentials
See `/app/memory/test_credentials.md`.

## Backlog (P1 / P2)
- P1: Make BidPanel and watchlist polling live (e.g. SSE or simple 10-s poll).
- P1: Persistent auto/proof file storage (S3 / disk). Currently we store only
  the filename + admin note; the binary is not retained.
- P1: Link won bids → existing CRM deals (currently only AutoInvoice and
  AutoLogisticsEvent are created; CRM linkage was deferred per spec §14).
- P2: Live auction countdown UI on vehicle cards.
- P2: i18n switch for EN/RU.
- P2: AI batch translation for newly-imported vehicles.
- P2: Webhook-based Stripe verification (currently relies on success-poll).

## Files added / modified
- Added: backend/models/auto.py, backend/services/auto_service.py,
  backend/services/auto_ai_service.py, backend/services/auto_import_service.py,
  backend/routes/auto_routes.py, backend/seed_auto.py,
  backend/tests/test_auto_backend.py.
- Modified: backend/server.py (router include + ensure_indexes),
  backend/.env (added EMERGENT_LLM_KEY, JWT_SECRET_KEY).
- Added: frontend/src/services/autoApi.js,
  frontend/src/pages/auto/{AutoLayout,AutoHome,AutoCatalog,AutoVehicleDetail,
  AutoDashboard,AutoAdmin,AutoHowItWorks,AutoFees,AutoAustralia}.jsx,
  frontend/src/pages/auto/auto.css,
  frontend/src/components/auto/{VehicleCard,VehicleFilters,BidPanel,
  DepositStatus,PriceBreakdown,LogisticsTimeline}.jsx.
- Modified: frontend/src/App.js (routes), frontend/src/components/Header.jsx
  (`Авто` link).
