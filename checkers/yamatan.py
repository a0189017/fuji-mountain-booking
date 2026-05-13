import logging
import re
from playwright.sync_api import Page
from .base import BaseChecker

log = logging.getLogger(__name__)

URL = "https://www.yamatan.net/en/hut/chojofujikan/plan?year=2026&month=07"

# Event title format (confirmed from live page):
# "○/Abeya (Japanese 相部屋)"   → available (many spots)
# "L16P/Abeya (Japanese 相部屋)" → limited: 16 people remaining
# "L1P/Abeya (Japanese 相部屋)"  → limited: 1 person remaining
# "×/Abeya (Japanese 相部屋)"   → full


class YamatanChecker(BaseChecker):
    name = "Yamatan 頂上富士館"
    url = URL

    def _is_available(self, page: Page) -> bool:
        # FullCalendar renders each date as td[data-date="YYYY-MM-DD"]
        try:
            page.wait_for_selector("[data-date='2026-07-31']", timeout=15000)
        except Exception:
            log.warning(f"[{self.name}] Timed out waiting for July 31 cell")
            return False

        day31_cell = page.query_selector("[data-date='2026-07-31']")
        if not day31_cell:
            log.info(f"[{self.name}] July 31 cell not found")
            return False

        event_titles = day31_cell.query_selector_all(".fc-event-title")
        if not event_titles:
            # No events = possibly no service that day
            log.info(f"[{self.name}] No events on July 31")
            return False

        for title_el in event_titles:
            text = (title_el.inner_text() or "").strip()
            log.info(f"[{self.name}] July 31 event: '{text}'")

            # Full
            if text.startswith("×"):
                continue

            # Definitely available (many spots)
            if text.startswith("○"):
                log.info(f"[{self.name}] July 31: ○ available!")
                return True

            # Limited: L{N}P/... where N >= target_people
            m = re.match(r"L(\d+)P", text)
            if m:
                remaining = int(m.group(1))
                if remaining >= self.target_people:
                    log.info(f"[{self.name}] July 31: {remaining} spots, enough for {self.target_people}!")
                    return True
                else:
                    log.info(f"[{self.name}] July 31: only {remaining} spot(s), need {self.target_people}")

        return False
