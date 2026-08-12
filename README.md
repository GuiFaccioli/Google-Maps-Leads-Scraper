# Google Maps Leads Scraper

## Open the project first

### Windows PowerShell — Terminal 1 (API/backend)

```powershell
cd "C:\Users\YOUR_USER\Desktop\google-maps-leads-scraper"
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="$PWD\src"
python -c "import asyncio; asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy()); import uvicorn; uvicorn.run('lead_scraper.api:app', host='127.0.0.1', port=8000)"
```

### Windows PowerShell — Terminal 2 (frontend)

```powershell
cd "C:\Users\YOUR_USER\Desktop\google-maps-leads-scraper\frontend"
npm run dev
```

Open `http://localhost:5173` in your browser.

> Bash is not required on Windows. If using Bash, activate the virtual environment with `source .venv/bin/activate` instead.

## First-time setup

Run these commands once from the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
playwright install
python scripts/init_db.py
cd frontend
npm install
```

## What the project does

The application searches Google Maps with Playwright, scrolls the results panel to collect more than the initial batch, opens each business page, and stores leads in SQLite.

Collected fields include:

- Business name
- Address
- Phone number
- Google Maps rating
- Number of reviews
- Google Maps URL
- Search query

The interface supports a result limit and optional minimum and maximum review filters.

## URLs

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- Leads endpoint: `http://localhost:8000/api/leads`

## Troubleshooting

### Playwright `NotImplementedError` on Windows

Start the backend with the PowerShell command shown above. The Proactor event-loop policy is required by Playwright when it launches the browser on Windows.

### The interface says the API is offline

Confirm that Terminal 1 is still running and that `http://localhost:8000/health` returns `{"status":"ok"}`.

### Old searches appear in a new search

The database keeps the full history, but the interface filters displayed leads by the current search query. Refresh the page with `Ctrl+F5` after restarting the backend.

## Development checks

```powershell
python -m compileall -f src
cd frontend
npm run build
```

## Project structure

```text
src/lead_scraper/   Python API, scraper, browser and database code
frontend/           React + Vite interface
scripts/init_db.py  Database initialization script
```
