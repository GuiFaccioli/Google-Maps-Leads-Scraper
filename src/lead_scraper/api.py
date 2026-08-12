from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from urllib.parse import quote_plus

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from lead_scraper.browser import BrowserSession, close_browser, open_browser
from lead_scraper.config import load_config
from lead_scraper.db import ensure_database, open_connection

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class JobState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScrapeJob:
    id: str
    query: str
    state: JobState
    leads_found: int = 0
    error: str | None = None
    created_at: str = ""


class ScrapeRequest(BaseModel):
    query: str = Field(min_length=2, max_length=200)
    limit: int = Field(default=20, ge=1, le=100)
    min_reviews: int | None = Field(default=None, ge=0)
    max_reviews: int | None = Field(default=None, ge=0)


class LeadResponse(BaseModel):
    id: int
    name: str
    phone: str | None = None
    address: str | None = None
    rating: float | None = None
    review_count: int | None = None
    price_range: str | None = None
    website: str | None = None
    category: str | None = None
    source_query: str | None = None
    source_url: str | None = None
    created_at: str
    updated_at: str


class JobResponse(BaseModel):
    id: str
    query: str
    state: JobState
    leads_found: int
    error: str | None
    created_at: str


config = load_config()
ensure_database(config.database_path)
app = FastAPI(title="Google Maps Leads Scraper API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

jobs: dict[str, ScrapeJob] = {}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/scrapes", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scrape(request: ScrapeRequest) -> ScrapeJob:
    job = ScrapeJob(
        id=str(uuid.uuid4()),
        query=request.query.strip(),
        state=JobState.PENDING,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    jobs[job.id] = job
    asyncio.create_task(_run_scrape(job, request.limit, request.min_reviews, request.max_reviews))
    return job


@app.get("/api/scrapes/{job_id}", response_model=JobResponse)
async def get_scrape(job_id: str) -> ScrapeJob:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Scrape job not found")
    return job


@app.get("/api/leads", response_model=list[LeadResponse])
async def list_leads(limit: int = 100, source_query: str | None = None) -> list[dict[str, Any]]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
    with open_connection(config.database_path) as connection:
        if source_query:
            rows = connection.execute(
                "SELECT * FROM leads WHERE LOWER(TRIM(source_query)) = LOWER(TRIM(?)) ORDER BY created_at DESC LIMIT ?",
                (source_query, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM leads ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(row) for row in rows]


async def _run_scrape(job: ScrapeJob, limit: int, min_reviews: int | None, max_reviews: int | None) -> None:
    session: BrowserSession | None = None
    job.state = JobState.RUNNING
    print(f"SCRAPE START {job.id}: {job.query}", flush=True)
    try:
        session = await open_browser()
        await session.page.goto(
            f"https://www.google.com/maps/search/{quote_plus(job.query)}",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await session.page.wait_for_timeout(1_200)
        link_data: list[tuple[str, str]] = []
        feed = session.page.locator('div[role="feed"]').first
        previous_count = 0
        unchanged_rounds = 0
        for _ in range(20):
            link_elements = await session.page.locator('a[href*="/maps/place/"]').all()
            known_urls = {item[1] for item in link_data}
            for link in link_elements:
                url = await link.get_attribute("href")
                name = (await link.inner_text()).strip()
                if url and name and url not in known_urls:
                    link_data.append((name, url))
                    known_urls.add(url)
                    if len(link_data) >= limit:
                        break
            if len(link_data) >= limit or await feed.count() == 0:
                break
            if len(link_data) == previous_count:
                unchanged_rounds += 1
            else:
                unchanged_rounds = 0
            if unchanged_rounds >= 3:
                break
            previous_count = len(link_data)
            await feed.evaluate("element => element.scrollTo(0, element.scrollHeight)")
            await session.page.wait_for_timeout(500)
        print(f"SCRAPE LINKS {job.id}: {len(link_data)}", flush=True)
        logger.info("Scrape %s: %d resultados encontrados na lista", job.id, len(link_data))
        leads: list[tuple[str, str, str | None, str | None, float | None, int | None, str | None, str | None]] = []
        seen_urls: set[str] = set()
        for name, url in link_data:
            if url not in seen_urls:
                seen_urls.add(url)
                await session.page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                await session.page.wait_for_timeout(700)
                address = await _detail_value(session.page, ['button[data-item-id="address"]', '[data-item-id="address"]'])
                phone = await _detail_value(session.page, ['button[data-item-id^="phone:"]', '[data-item-id^="phone:"]'])
                rating, review_count = await _review_data(session.page)
                price_range = await _price_range(session.page)
                website = await _detail_value(session.page, ['a[data-item-id="authority"]', '[data-item-id="authority"]'])
                print(f"SCRAPE DATA {job.id}: {name} | {address=} {phone=} {rating=} {review_count=} {price_range=} {website=}", flush=True)
                logger.info("Scrape %s: %s | address=%r phone=%r rating=%r reviews=%r", job.id, name, address, phone, rating, review_count)
                if (min_reviews is not None and (review_count is None or review_count < min_reviews)) or (max_reviews is not None and (review_count is None or review_count > max_reviews)):
                    continue
                leads.append((name, url, address, phone, rating, review_count, price_range, website))
            if len(leads) >= limit:
                break

        with open_connection(config.database_path) as connection:
            for name, url, address, phone, rating, review_count, price_range, website in leads:
                connection.execute(
                    "INSERT INTO leads (name, address, phone, rating, review_count, price_range, website, source_query, source_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(name, address, phone) DO UPDATE SET rating=excluded.rating, review_count=excluded.review_count, price_range=excluded.price_range, website=excluded.website, source_query=excluded.source_query, source_url=excluded.source_url, updated_at=datetime('now')",
                    (name, address, phone, rating, review_count, price_range, website, job.query, url),
                )
            connection.commit()
        print(f"SCRAPE SAVED {job.id}: {len(leads)} leads in {config.database_path}", flush=True)
        job.leads_found = len(leads)
        job.state = JobState.COMPLETED
    except Exception:
        logger.exception("Scrape %s failed", job.id)
        job.state = JobState.FAILED
        job.error = "Scrape failed. Check the API logs for details."
    finally:
        await close_browser(session)


async def _detail_value(page: Any, selectors: list[str]) -> str | None:
    for selector in selectors:
        element = page.locator(selector).first
        if await element.count() == 0:
            continue
        value = await element.get_attribute("aria-label") or await element.inner_text()
        if value:
            return value.removeprefix("Endereço: ").removeprefix("Telefone: ").strip()
    return None


async def _review_data(page: Any) -> tuple[float | None, int | None]:
    import re
    candidates = [
        'button[jsaction*="reviewChart"]',
        '[aria-label*="avalia"]',
        '[aria-label*="review"]',
        'div.F7nice',
    ]
    values: list[str] = []
    for selector in candidates:
        for element in await page.locator(selector).all():
            value = await element.get_attribute("aria-label") or await element.inner_text()
            if value and value not in values:
                values.append(value)
    text = " ".join(values)
    normalized_text = " ".join(text.replace("\xa0", " ").split())
    rating_match = re.search(r"(\d[,.]\d)", normalized_text)
    count_match = re.search(r"\(([\d.,]+)\)", normalized_text)
    if count_match is None:
        count_match = re.search(r"([\d.,]+)\s*(?:avaliações|avaliações do Google|reviews?)", normalized_text, re.IGNORECASE)
    if count_match is None:
        numbers = re.findall(r"\b\d[\d.,]*\b", normalized_text)
        candidates = [value for value in numbers if not re.fullmatch(r"\d[,.]\d", value)]
        if candidates:
            count_match = re.search(f"({re.escape(candidates[-1])})", normalized_text)
    rating = float(rating_match.group(1).replace(",", ".")) if rating_match else None
    review_count = None
    if count_match:
        raw_count = count_match.group(1).replace(".", "").replace(",", "")
        if raw_count.isdigit():
            review_count = int(raw_count)
    print(f"SCRAPE REVIEWS: raw={normalized_text!r} parsed={review_count}", flush=True)
    return rating, review_count


async def _price_range(page: Any) -> str | None:
    import re
    text = await page.locator("body").inner_text()
    match = re.search(r"R\$\s*[\d.]+(?:,\d+)?\s*[-–—]\s*R\$?\s*[\d.]+(?:,\d+)?", text, re.IGNORECASE)
    return " ".join(match.group(0).split()) if match else None
