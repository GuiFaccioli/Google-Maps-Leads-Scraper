from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright


@dataclass
class BrowserSession:
    playwright: any
    browser: Browser
    context: BrowserContext
    page: Page


async def open_browser(headless: bool = True) -> BrowserSession:
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context()
    page = await context.new_page()
    return BrowserSession(playwright=playwright, browser=browser, context=context, page=page)


async def close_browser(session: Optional[BrowserSession]) -> None:
    if session is None:
        return
    await session.context.close()
    await session.browser.close()
    await session.playwright.stop()
