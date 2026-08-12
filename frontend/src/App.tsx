import { FormEvent, useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type JobState = "pending" | "running" | "completed" | "failed";

type Lead = {
  id: number;
  name: string;
  address: string | null;
  phone: string | null;
  source_query: string | null;
  source_url: string | null;
  rating: number | null;
  review_count: number | null;
  price_range: string | null;
  website: string | null;
};

type Job = {
  id: string;
  query: string;
  state: JobState;
  leads_found: number;
  error: string | null;
};

const stateLabels: Record<JobState, string> = {
  pending: "Na fila",
  running: "Coletando",
  completed: "Concluído",
  failed: "Falhou",
};

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? "Não foi possível concluir a solicitação.";
  } catch {
    return "Não foi possível conectar à API.";
  }
}

function App() {
  const [query, setQuery] = useState("restaurantes em São Paulo");
  const [limit, setLimit] = useState("20");
  const [minReviews, setMinReviews] = useState("");
  const [maxReviews, setMaxReviews] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copyLabel, setCopyLabel] = useState("Copiar lista");

  useEffect(() => {
    void fetch(`${API_URL}/health`)
      .then((response) => setApiOnline(response.ok))
      .catch(() => setApiOnline(false));
  }, []);

  useEffect(() => {
    if (!job || (job.state !== "pending" && job.state !== "running")) return;

    const timer = window.setInterval(() => {
      void fetch(`${API_URL}/api/scrapes/${job.id}`)
        .then(async (response) => {
          if (!response.ok) throw new Error(await readError(response));
          return response.json() as Promise<Job>;
        })
        .then((nextJob) => setJob(nextJob))
        .catch((requestError: Error) => setError(requestError.message));
    }, 2000);

    return () => window.clearInterval(timer);
  }, [job]);

  useEffect(() => {
    if (job?.state !== "completed") return;
      void loadLeads(job.query);
  }, [job?.state]);

  async function loadLeads(sourceQuery?: string) {
    try {
      const query = sourceQuery ? `&source_query=${encodeURIComponent(sourceQuery)}` : "";
      const response = await fetch(`${API_URL}/api/leads?limit=100${query}`);
      if (!response.ok) throw new Error(await readError(response));
      setLeads((await response.json()) as Lead[]);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Erro ao carregar leads.");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setJob(null);
    try {
      const response = await fetch(`${API_URL}/api/scrapes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), limit: Number(limit), min_reviews: minReviews ? Number(minReviews) : null, max_reviews: maxReviews ? Number(maxReviews) : null }),
      });
      if (!response.ok) throw new Error(await readError(response));
      setJob((await response.json()) as Job);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Erro ao iniciar coleta.");
    } finally {
      setIsLoading(false);
    }
  }

  async function copyLeads() {
    const text = leads.map((lead) => `${lead.name}\n${lead.address ?? "Endereço não informado"}\n${lead.phone ?? "Telefone não informado"} · Nota: ${lead.rating ?? "—"} · ${lead.review_count ?? 0} avaliações · ${lead.price_range ?? "Preço não informado"}\n${lead.website ?? "Website não informado"}`).join("\n\n");
    await navigator.clipboard.writeText(text);
    setCopyLabel("Lista copiada");
    window.setTimeout(() => setCopyLabel("Copiar lista"), 1800);
  }

  /*
    const text = leads.map((lead) => [
      lead.name,
      lead.phone ?? "Telefone não informado",
      lead.address ?? "Endereço não informado",
      `Nota: ${lead.rating ?? "—"}`,
      `${lead.review_count ?? 0} avaliações`,
      lead.price_range ?? "Preço não informado",
      lead.website ?? "Website não informado",
      lead.source_url ?? "",
    ].join(" | ")).join("\n");
    await navigator.clipboard.writeText(text);
    setCopyLabel("Lista copiada");
    window.setTimeout(() => setCopyLabel("Copiar lista"), 1800);
  */

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Maps Leads início">
          <span className="brand-mark">M</span>
          <span>MAPS LEADS</span>
        </a>
        <span className={apiOnline ? "api-status online" : "api-status"}>
          <span className="status-dot" aria-hidden="true" />
          {apiOnline ? "API online" : "API offline"}
        </span>
      </header>

      <main className="content">
        <section className="hero" aria-labelledby="page-title">
          <p className="eyebrow">GOOGLE MAPS / LEAD GENERATION</p>
          <h1 id="page-title">Encontre negócios.<br /><span>Encontre oportunidades.</span></h1>
          <p className="hero-copy">Pesquise no Google Maps e transforme resultados locais em uma lista de leads organizada.</p>
        </section>

        <section className="panel search-panel" aria-labelledby="search-title">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">01 / PESQUISA</p>
              <h2 id="search-title">O que você está procurando?</h2>
            </div>
            <span className="panel-number">⌕</span>
          </div>
          <form onSubmit={handleSubmit}>
            <label htmlFor="query">Termo de busca</label>
            <div className="form-row">
              <input id="query" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ex.: dentistas em Campinas" required minLength={2} />
              <label htmlFor="min-reviews">Avaliações mínimas<input id="min-reviews" type="number" min="0" value={minReviews} onChange={(event) => setMinReviews(event.target.value)} /></label>
              <label htmlFor="max-reviews">Avaliações máximas<input id="max-reviews" type="number" min="0" value={maxReviews} onChange={(event) => setMaxReviews(event.target.value)} /></label>
              <label className="limit-field" htmlFor="limit">Limite
                <input id="limit" type="number" min="1" max="100" value={limit} onChange={(event) => setLimit(event.target.value)} />
              </label>
              <button className="primary-button" type="submit" disabled={isLoading || !apiOnline}>
                {isLoading ? "Iniciando..." : "Iniciar coleta"}<span aria-hidden="true">→</span>
              </button>
            </div>
          </form>
          {error && <p className="error-message" role="alert">{error}</p>}
        </section>

        <section className="results-section" aria-labelledby="results-title">
          <div className="section-header">
            <div><p className="section-kicker">02 / RESULTADOS</p><h2 id="results-title">Leads coletados</h2></div>
            <div className="results-actions"><span className="result-count">{leads.length.toString().padStart(2, "0")}</span><button className="copy-button" type="button" onClick={() => void copyLeads()} disabled={leads.length === 0}>{copyLabel}</button></div>
          </div>
          {job && <div className="job-status"><span className={`state-badge ${job.state}`}><span className="status-dot" />{stateLabels[job.state]}</span><span>{job.query} · {job.leads_found} encontrados</span></div>}
          {leads.length === 0 ? <div className="empty-state">{job?.state === "pending" || job?.state === "running" ? <><span className="loading-spinner" aria-hidden="true" /><p>Coletando leads...</p><span>O Google Maps está sendo consultado.</span></> : <><span className="empty-icon">◌</span><p>Nenhum lead coletado ainda.</p><span>Faça uma pesquisa para começar.</span></>}</div> : <div className="lead-list">{leads.map((lead) => <article className="lead-card" key={lead.id}><div><h3>{lead.name}</h3><p>{lead.address ?? "Endereço não informado"}</p><p>{lead.phone ?? "Telefone não informado"} · Nota: {lead.rating ?? "—"} · {lead.review_count ?? 0} avaliações · {lead.price_range ?? "Preço não informado"}</p>{lead.website ? <a className="lead-website" href={lead.website} target="_blank" rel="noreferrer">Website ↗</a> : <p>Website não informado</p>}</div>{lead.source_url && <a href={lead.source_url} target="_blank" rel="noreferrer">Ver no Maps ↗</a>}</article>)}</div>}
        </section>
      </main>
      <footer><span>LOCAL TOOL / v0.1.0</span><span>Feito para prospecção inteligente.</span></footer>
    </div>
  );
}

export default App;
