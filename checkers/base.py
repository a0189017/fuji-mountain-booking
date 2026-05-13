import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

log = logging.getLogger(__name__)


class BaseChecker(ABC):
    name: str
    url: str

    def __init__(self, config: dict):
        self.config = config
        self.debug = config.get("DEBUG", "false").lower() == "true"
        self.target_date = int(config.get("TARGET_DATE", "31"))
        self.target_people = int(config.get("TARGET_PEOPLE", "2"))

    def check(self) -> bool:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not self.debug)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/124.0.0.0 Safari/537.36",
                locale="ja-JP",
            )
            page = context.new_page()
            try:
                page.goto(self.url, wait_until="networkidle", timeout=30000)
                if self.debug:
                    self._save_debug(page)
                return self._is_available(page)
            finally:
                browser.close()

    def _save_debug(self, page: Page):
        debug_dir = Path("debug")
        debug_dir.mkdir(exist_ok=True)
        safe_name = self.name.replace(" ", "_").lower()
        page.screenshot(path=str(debug_dir / f"{safe_name}.png"), full_page=True)
        html = page.content()
        with open(debug_dir / f"{safe_name}.html", "w", encoding="utf-8") as f:
            f.write(html)
        log.info(f"[{self.name}] Debug files saved to debug/{safe_name}.*")

    @abstractmethod
    def _is_available(self, page: Page) -> bool:
        """Return True if TARGET_DATE has availability for TARGET_PEOPLE."""
