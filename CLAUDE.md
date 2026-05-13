# Ruffy 2.0 — Brainstorm Sandbox

**This is exploratory. Mock data only. Zero connection to live Ruffy code or services. Do not link or reference from `~/ruffy/`.**

## What this is
The umbrella folder for Ruffy 2.0 prototyping. Components live as sibling subfolders; the first one is `clinic-portal/`. As the 2.0 vision develops, other components (parent storefront, comms inbox, ops surfaces) will land here as siblings.

## Components
| Folder | Description | Status |
|---|---|---|
| `clinic-portal/` | Vet clinic portal — home, renewals, new rx composer with describe/manual modes + taper module + autoship, clients, orders, products, invoices | Live prototype at https://ruffy-2-0.streamlit.app |

## Deploy
The repo is on GitHub at https://github.com/Rafi-Ruffy/ruffy-2.0 and auto-deploys to Streamlit Community Cloud on every push to `main`. The `ANTHROPIC_API_KEY` is set in Streamlit Cloud's secrets (not in this repo).

## Rules for working in this folder
- Stay isolated from `~/ruffy/`. Don't import production code, don't reference live data, don't edit `~/ruffy/CLAUDE.md` to point at this.
- Mock data only. Live data integrations are out of scope for the brainstorm.
- Visual design follows KoalaVet's calm aesthetic — serif headers (Georgia), soft palette, generous whitespace.

See `clinic-portal/CLAUDE.md` for per-component design intent and file layout.
