# Ruffy 2.0 — Clinic Portal Prototype

**Brainstorm sandbox. Zero connection to live Ruffy code, database, or services.** All data is invented in `mock_data.py`.

## What this is
A Streamlit prototype of the Ruffy 2.0 clinic portal. The mental model: modern rebuild of Vetsource — same core workflows (client/pet management, write rxs, approve refill requests, track orders, see payouts) but Canadian, designed for autoship-default, with a calm KoalaVet-style aesthetic instead of Vetsource's web-1.0 form-and-page-reload feel.

## Live demo
https://ruffy-2-0.streamlit.app — auto-deployed from `main` on every push to https://github.com/Rafi-Ruffy/ruffy-2.0. The `ANTHROPIC_API_KEY` is stored in Streamlit Cloud's secret manager (not in the repo).

## How to run locally
Double-click `Ruffy Clinic Portal 2.0.command` on the Desktop, or:
```bash
cd ~/ruffy-2.0/clinic-portal
python3 -m streamlit run app.py --server.port 8506
```
The `ANTHROPIC_API_KEY` env var enables real LLM extraction in the New Rx "Describe" mode. Without it, falls back to a regex/keyword mock parser.

## How to push updates
```bash
cd ~/ruffy-2.0
git add -A && git commit -m "your message" && git push
```
Streamlit Cloud auto-redeploys in ~1 minute.

## Surfaces

**Sidebar**: Start-a-new-rx (primary button) · Renewals (with count badge) · Home · Renewals · New Rx · Clients · Order history · Products · Invoices

**Home** — dashboard
- 4 KPI tiles: AutoShip renewals / Client refill requests / Orders in flight / Delivered this month
- "Start a new prescription" quickstart (client search → start)
- Renewal queue with source badges (AutoShip renewal = system-initiated; Client request = client-initiated)
- Recent orders strip at the bottom

**Renewals** — dedicated queue
- Pending tab split into two sections: AutoShip renewals and Client-initiated refill requests
- Approve modal: full clinical context (weight, age, previous rx, autoship history) + editable refills/expiry/notes/instructions
- Deny modal: structured reason dropdown (Incorrect product/strength/qty, Pet due for exam, Pet passed away/rehomed, Not clinically appropriate, Other)
- Decided tab shows approved/denied history with reasons

**New Rx** — composer
- Step 1 Client → Step 2 Patient (explicit pet selection card) → Step 3 Prescription
- Two modes: "Describe in your own words" (Claude extracts to structured fields) OR "Build manually" (form)
- Drug maps to real catalog (fuzzy match)
- Dose + Frequency structured fields with bidirectional sync to Instructions text (edit any one, others stay consistent; vet's custom additions like "with food" preserved)
- Multi-phase/tapered rx toggle: dynamic phase builder (+ Add phase / Remove), auto-computes first-fill, maintenance-per-cycle, total authorized, and label instructions joined with "then"
- AutoShip section: optional checkbox + frequency + first ship date
- Approval section: pre-approve with vet + PIN OR send to approval queue

**Clients** — directory
- Search by client or pet name
- Drill in to per-client view: pet cards + full order history

**Order history** — log of every rx sent to Ruffy with status pills (Awaiting payment / Shipped / Delivered / Processing) and segmented filter

**Products** — Ruffy catalog with retail price ranges and stock status

**Invoices** — monthly payouts to the clinic

## Design intent / aesthetic
- Calm KoalaVet-style: serif headers (Georgia), soft white/mint palette, generous whitespace, one CTA per row, pill-shaped status badges
- No urgent badges or AI clutter
- Information hierarchy first, polish second

## v1.0 workflow assumptions
- Clinic ORIGINATES rxs (vet writes them; CE may enter with pre-approval)
- Renewals queue is for clients out of refills — either system-detected (autoship running low) or client-initiated (manual refill request)
- Vet must approve every renewal (Canadian regulatory requirement — no auto-approval)
- AutoShip is incentivized but not defaulted (client choice at checkout in v2; vet can also set it up at rx time)
- Any-quantity assumption: catalog supports flexible quantities (Koala-style, not Vetsource sealed-pack-only)
- Client-side storefront is v2 (out of scope here)
- Comms inbox is v2 (no two-way parent-clinic messaging surface yet)

## Files
| File | Purpose |
|---|---|
| `app.py` | Entry, navigation, sidebar shell |
| `mock_data.py` | All invented data (clinic, vets, clients, pets, orders, renewals, products) |
| `views/home.py` | Home: KPI tiles + quickstart + renewal queue + recent orders |
| `views/renewals.py` | Dedicated renewals queue with pending/decided tabs |
| `views/new_rx.py` | Multi-step rx composer with describe/manual modes + taper module + autoship + approval |
| `views/clients.py` | Client directory + per-client detail |
| `views/orders.py` | Order history with filter pills |
| `views/products.py` | Catalog list |
| `views/invoices.py` | Monthly payout list |
