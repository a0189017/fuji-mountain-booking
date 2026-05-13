import logging
import re
from playwright.sync_api import Page
from .base import BaseChecker

log = logging.getLogger(__name__)

URL = "https://www.goraikoukan.jp/?y=2026&m=07"

AVAILABLE_MARK = "○"
UNAVAILABLE_MARK = "×"


class GoraikoukanChecker(BaseChecker):
    name = "御来光館 (Goraikoukan)"
    url = URL

    def _is_available(self, page: Page) -> bool:
        # Calendar structure:
        # Simple table grid with dates 1-31, each cell showing ○ or ×
        # Instructions say: "カレンダー「○」印をクリックしてください"
        # Available dates have clickable ○ links; unavailable dates show ×

        try:
            page.wait_for_selector("table, .calendar", timeout=10000)
        except Exception:
            log.warning(f"[{self.name}] Timed out waiting for calendar")

        # Strategy 1: Find anchor tags with ○ near day 31
        # Available dates are clickable links
        all_links = page.query_selector_all("a")
        for link in all_links:
            href = link.get_attribute("href") or ""
            text = (link.inner_text() or "").strip()
            # Look for ○ link that references July 31
            if AVAILABLE_MARK in text and ("31" in href or "0731" in href):
                log.info(f"[{self.name}] Day 31: booking link with ○ found!")
                return True

        # Strategy 2: Find the table cell for day 31 with ○
        cells = page.query_selector_all("td, .day, [class*='day']")
        for cell in cells:
            text = (cell.inner_text() or "").strip()
            lines = text.split('\n')

            # Check if this cell represents day 31
            first_line = lines[0].strip() if lines else ""
            if first_line != "31" and not re.fullmatch(r'31', first_line):
                continue

            log.info(f"[{self.name}] Found day 31 cell: '{text[:100]}'")

            # Check for available mark
            if AVAILABLE_MARK in text:
                log.info(f"[{self.name}] Day 31: ○ found, available!")
                return True

            # Check for clickable link inside this cell
            inner_link = cell.query_selector("a")
            if inner_link:
                log.info(f"[{self.name}] Day 31: has booking link!")
                return True

            if UNAVAILABLE_MARK in text:
                log.info(f"[{self.name}] Day 31: × found, unavailable")
                return False

        # Strategy 3: Parse full page content
        content = page.content()
        # Find pattern where 31 and ○ appear together
        # Common HTML: <td>31<br>○</td> or <td class="available">31</td>
        if re.search(r'31[^0-9]*○|○[^0-9]*31', content):
            # Verify it's in context of July (not another month)
            if '2026' in content or '7月' in content or 'July' in content:
                log.info(f"[{self.name}] Day 31: found ○ near 31 in page content")
                return True

        log.info(f"[{self.name}] Day 31: not available")
        return False
