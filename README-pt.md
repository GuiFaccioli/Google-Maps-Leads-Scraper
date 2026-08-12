# Google Maps Leads Scraper

## Como abrir o projeto

### Windows PowerShell — Terminal 1 (API/backend)

```powershell
cd "C:\Users\SEU_USUARIO\Desktop\google-maps-leads-scraper"
\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="$PWD\src"
python -c "import asyncio; asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy()); import uvicorn; uvicorn.run('lead_scraper.api:app', host='127.0.0.1', port=8000)"
```

### Windows PowerShell — Terminal 2 (frontend)

```powershell
cd "C:\Users\SEU_USUARIO\Desktop\google-maps-leads-scraper\frontend"
npm run dev
```

Abra `http://localhost:5173` no navegador.

> No Windows, Bash não é necessário. Se estiver usando Bash, ative o ambiente virtual com `source .venv/bin/activate`.

## Configuração inicial

Execute uma vez, no PowerShell e na raiz do projeto:

```powershell
python -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install -e .
playwright install
python scripts/init_db.py
cd frontend
npm install
```

## O que o projeto faz

O sistema pesquisa no Google Maps usando Playwright, rola o painel de resultados para buscar mais empresas, abre a página de cada negócio e salva os leads em SQLite.

Dados coletados:

- Nome do negócio
- Endereço
- Telefone
- Nota do Google Maps
- Quantidade de avaliações
- Link do Google Maps
- Termo pesquisado

A interface permite configurar o limite de resultados e filtros opcionais de avaliações mínimas e máximas.

## Endereços

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- Leads: `http://localhost:8000/api/leads`

## Solução de problemas

### Erro `NotImplementedError` no Playwright

Inicie o backend usando o comando do Terminal 1 acima. A política Proactor é necessária para o Playwright abrir o navegador no Windows.

### A interface mostra a API offline

Verifique se o Terminal 1 continua aberto e se `http://localhost:8000/health` retorna `{"status":"ok"}`.

### Pesquisas antigas aparecem junto da nova

O banco mantém todo o histórico, mas a interface filtra os resultados pela pesquisa atual. Atualize a página com `Ctrl+F5` após reiniciar o backend.

## Verificações de desenvolvimento

```powershell
python -m compileall -f src
cd frontend
npm run build
```

## Estrutura do projeto

```text
src/lead_scraper/   API Python, scraper, navegador e banco de dados
frontend/           Interface React + Vite
scripts/init_db.py  Script de inicialização do banco
```
