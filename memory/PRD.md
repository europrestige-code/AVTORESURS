# BuyAnywhere Auto / АвтоРесурс — PRD

## Brand
- **Platform**: BuyAnywhere
- **Product**: BuyAnywhere Auto (publicly branded as **АвтоРесурс**, tagline "АВТОМОБИЛИ СО ВСЕГО МИРА")
- **Technical namespace**: `/auto`
- **Logo assets**: `/app/frontend/public/branding/avtoresurs-mark.png`,
  `/app/frontend/public/branding/avtoresurs-wordmark.png`

## Original problem statement
Russian-language vehicle sourcing + internal proxy-bidding platform for NZ
vehicles (auction + fixed price + damaged + end-of-life), AU inquiry-only.
Reuse existing FastAPI + React + MongoDB + JWT stack; no new auth / DB /
framework.

## Architecture
- Backend (`/api/auto`) — modular service layer:
  - `auto_service` (bidding, deposits, pricing, CRM linkage)
  - `auto_ai_service` (extract / translate / risk summary; GPT-5.2)
  - `auto_import_service` (text / URL / CSV importer)
  - `auto_source_importers` (Turners / Manheim / Pickles)
  - `auto_transport_service` (NZ city tariff + ×2 non-runner rule)
  - `auto_auctions_service` (Turners calendar scrape + persistence)
  - `auto_image_service` (АвтоРесурс branded frame overlay)
- Mongo collections: `auto_vehicles`, `auto_bids`, `auto_deposits`,
  `auto_inquiries`, `auto_invoices`, `auto_logistics_events`,
  `auto_watchlist`, `auto_auction_calendar`, `auto_import_runs`
- Frontend (React) — dark premium theme scoped to `.auto-root`
- Auth: shared JWT (no separate auth)
- Payments: Stripe (test key) Checkout + manual deposit proof workflow

## Business rules
- Deposit NZ$1,000 required to bid; one verified deposit grants bidding
- Bidding allowed only on country=NZ, listing_type=auction, status=available
- New bid must be > current active highest; equal bids rejected with exact
  Russian message
- Previous active bids on a vehicle automatically marked `outbid`
- Australia listings are inquiry-only
- Pricing formula:
  `price + 20% commission + transport(city, non_runner) + forklift + storage·50 + docs 250 + container 3333`
- Transport pricing: city-aware (Auckland $0 → Invercargill $1,950).
  **Non-runner = ×2 transport** (towing surcharge).

## What's been implemented (2026-01)
- ✅ Backend models, services, routes per spec
- ✅ Internal proxy bidding with deposit gate and outbid handling
- ✅ Manual + Stripe deposit verify workflow with real file storage on disk
- ✅ Watchlist / inquiries / invoices / logistics events
- ✅ AI extraction / RU translation / risk summary (with fallback model)
- ✅ Importer from text / URL / CSV (graceful Russian fallback when fetch fails)
- ✅ Source Importer abstraction + concrete Turners / Manheim / Pickles
- ✅ Duplicate detection (source+ref → VIN → year+make+model+mileage+location)
- ✅ Won-bid → CRMOrder linkage (idempotent, `source='buyanywhere_auto'`)
- ✅ Real file storage for deposit proofs (`backend/uploads/deposits/`)
- ✅ Live auction countdowns + live bid polling (8s)
- ✅ АвтоРесурс branding (logo, tagline, header, footer, Terms page)
- ✅ **Turners auctions calendar** (`/api/auto/auctions/calendar`) — 24
   branch pages scraped, 47+ events over 21 days, by-day buckets with lot
   counts and cities
- ✅ **Transport pricing engine** (`/api/auto/transport/cost`) — 30+ cities
   with PTS-style tariffs; ×2 for non-runners
- ✅ **АвтоРесурс branded image frame** — overlays our logo + source
   attribution; does NOT remove third-party watermarks (legal compliance)
- ✅ **Category separation** (`/auto/auctions-list`, `/auto/buynow`,
   `/auto/damaged`, `/auto/end-of-life`, `/auto/parts`) — aggregates across
   ALL sources
- ✅ **Terms & Conditions** (`/auto/terms`) — 8 sections stating purchase
   is with АвтоРесурс (not the source auction)
- ✅ Vehicle card visual alignment rewrite — fixed image ratio, clamped
   title height, price row at bottom, full-width CTA
- ✅ Turners-style **Search Hero** with body-type chips, make/model/year
   selectors, and category tiles
- ✅ React Routes: index / catalog / vehicle/:id / dashboard / admin /
   how-it-works / fees / australia / auctions / terms / auctions-list /
   buynow / damaged / end-of-life / parts

## Test results (iter 2)
- **Backend**: 11/11 pytest passing
- **Frontend**: 100% of targeted flows verified
- Test credentials: `/app/memory/test_credentials.md`

## Source-importer roadmap (per architecture brief)
**Phase 1**: NZ vehicles — DONE structurally. Turners scraping live; Manheim
& Pickles importers in place (graceful empty result when site changes).
**Phase 2**: Australia vehicles — basic Pickles importer; expand to other AU
auctions.
**Phase 3**: Parts and donor vehicles — placeholder route `/auto/parts`.
**Phase 4**: Japanese auctions — add `JpAuctionImporter` against `IMPORTERS`
registry. No core changes needed.
**Phase 5**: Heavy machinery — add a new vertical under `/auto/machinery` or
a sibling product (BuyAnywhere Machinery).

## Backlog
- **P1**: Daily scheduled refresh of Turners calendar (currently manual /
  admin button).
- **P1**: Live source-importer admin UI (run Turners/Manheim/Pickles,
  review extracted vehicles, save batch).
- **P1**: Pre-flight image branding (run on import; backfill button for
  existing rows).
- **P1**: Notification when a bid is outbid (email / Telegram).
- **P2**: Map view for auctions calendar.
- **P2**: VIN decoder integration for canonical make/model/year.
- **P2**: Currency live rate (FX RUB/NZD) refresh.
- **P2**: Saved searches + email alerts.
