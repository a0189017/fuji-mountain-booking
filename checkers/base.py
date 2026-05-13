import logging
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

log = logging.getLogger(__name__)

# Path to system Chrome/Chromium, used in CI to skip playwright install.
# e.g. /usr/bin/google-chrome-stable on ubuntu-latest GitHub Actions runners.
_CHROME_PATH = os.environ.get("CHROME_PATH") or None


class BaseChecker:
    name: str
    url: str

    def __init__(self, config: dict):
        self.config = config
        self.debug = config.get("DEBUG", "false").lower() == "true"
        self.target_date = int(config.get("TARGET_DATE", "31"))
        self.target_people = int(config.get("TARGET_PEOPLE", "2"))

    def check(self) -> bool:
        """Default implementation uses Playwright. Subclasses may override entirely."""
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=_CHROME_PATH,
                headless=not self.debug,
            )
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
                    self._save_debug_playwright(page)
                return self._is_available(page)
            finally:
                browser.close()

    def _is_available(self, page: Page) -> bool:
        raise NotImplementedError

    def _save_debug_playwright(self, page: Page):
        self._save_debug_html(page.content(), self.name)
        debug_dir = Path("debug")
        page.screenshot(path=str(debug_dir / f"{self._safe_name()}.png"), full_page=True)

    def _save_debug_html(self, html: str, label: str):
        debug_dir = Path("debug")
        debug_dir.mkdir(exist_ok=True)
        path = debug_dir / f"{self._safe_name()}.html"
        path.write_text(html, encoding="utf-8")
        log.info("[%s] Debug HTML saved to %s", self.name, path)

    def _safe_name(self) -> str:
        return self.name.replace(" ", "_").replace("/", "_")
