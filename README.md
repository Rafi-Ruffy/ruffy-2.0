# Ruffy 2.0

Brainstorm sandbox for the Ruffy 2.0 platform vision. Mock data only — zero connection to any live Ruffy data, services, or production code.

## What's in here

| Folder | Purpose |
|---|---|
| `clinic-portal/` | Streamlit prototype of the Ruffy 2.0 clinic-facing portal. The first piece of the 2.0 vision. Modeled on KoalaVet's calm aesthetic with same core workflows as Vetsource but redesigned for autoship-default, Canadian pharmacy operations, and an LLM-assisted prescribing flow. |

More 2.0 components (parent storefront, comms inbox, etc.) will live as siblings under this root.

## Live demo
https://ruffy-2-0.streamlit.app — auto-deployed from this repo's `main` branch via Streamlit Community Cloud.

## Running locally
```bash
cd clinic-portal
python3 -m streamlit run app.py --server.port 8506
```
Set `ANTHROPIC_API_KEY` in your env for the AI rx extraction; without it, the app falls back to a regex parser.

## Updating the deployed app
Just push to `main`:
```bash
git add . && git commit -m "your change" && git push
```
Streamlit Cloud rebuilds and redeploys in ~1 minute.

## Per-component docs
Each subfolder has its own `CLAUDE.md` with the design intent, data model, and file layout.
