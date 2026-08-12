# Google Maps Leads Scraper

## Descrição

Ferramenta local para pesquisar empresas no Google Maps e organizar leads comerciais com nome, endereço, telefone, nota, quantidade de avaliações e link do Maps.

## Como abrir o projeto

### Primeira execução — PowerShell

Execute uma vez, na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
playwright install
python scripts/init_db.py
cd frontend
npm install
```

### Terminal 1 — API/backend

```powershell
cd "C:\Users\YOUR_USER\Desktop\google-maps-leads-scraper"
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="$PWD\src"
python -c "import asyncio; asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy()); import uvicorn; uvicorn.run('lead_scraper.api:app', host='127.0.0.1', port=8000)"
```

### Terminal 2 — frontend

```powershell
cd "C:\Users\YOUR_USER\Desktop\google-maps-leads-scraper\frontend"
npm run dev
```

Abra no navegador:

```text
http://localhost:5173
```

## Tecnologias usadas

- Python
- FastAPI
- Playwright
- SQLite
- React
- TypeScript
- Vite

## Para que serve

O sistema pesquisa resultados no Google Maps, rola a lista para encontrar mais empresas, abre os detalhes de cada negócio e salva os leads localmente em SQLite.

Os dados coletados incluem:

- Nome
- Endereço
- Telefone
- Nota do Google Maps
- Quantidade de avaliações
- Link do Google Maps
- Termo pesquisado

A interface permite definir o limite de resultados, filtrar pela quantidade de avaliações e copiar a lista de leads.
