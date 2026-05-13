import logging
import requests
from bs4 import BeautifulSoup
from .base import BaseChecker

log = logging.getLogger(__name__)

URL = "https://www.goraikoukan.jp/?y=2026&m=07"

AVAILABLE_MARK = "○"
UNAVAILABLE_MARK = "×"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
}


class GoraikoukanChecker(BaseChecker):
    name = "御来光館 (Goraikoukan)"
    url = URL

    def check(self) -> bool:
        resp = requests.get(self.url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        if self.debug:
            self._save_debug_html(resp.text, "goraikoukan")

        # Calendar: <td class="bat"><span>31</span>×</td>
        # Available: the × becomes a clickable ○ link
        for td in soup.find_all("td"):
            span = td.find("span")
            if not span or span.get_text(strip=True) != "31":
                continue

            cell_text = td.get_text(strip=True)
            log.info("[%s] Found day 31 cell: '%s'", self.name, cell_text)

            if AVAILABLE_MARK in cell_text or td.find("a"):
                log.info("[%s] Day 31: ○ available!", self.name)
                return True

            log.info("[%s] Day 31: unavailable", self.name)
            return False

        log.info("[%s] Day 31 not found in calendar", self.name)
        return False
