import logging
import requests
from bs4 import BeautifulSoup
from .base import BaseChecker

log = logging.getLogger(__name__)

URL = "https://tomoekan.com/8tomoekan-calender/?ct=1782864000"

# HTML structure (confirmed from live page):
# <td class="day-31 fri on">
#   <div class="room-daily">
#     <span class="room-name room-id-6002">八ﾄﾓ2名</span>
#     <span class="room-status full">×</span>   ← full
#     or
#     <span class="room-status">〇</span>       ← available
#   </div>
# </td>
ROOM_2P_CLASS = "room-id-6002"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
}


class TomoekanChecker(BaseChecker):
    name = "巴館 (Tomoekan)"
    url = URL

    def check(self) -> bool:
        resp = requests.get(self.url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        if self.debug:
            self._save_debug_html(resp.text, "tomoekan")

        day31_cell = soup.find("td", class_=lambda c: c and "day-31" in c.split())
        if not day31_cell:
            log.info("[%s] Day 31 cell not found", self.name)
            return False

        room_2p = day31_cell.find(class_=ROOM_2P_CLASS)
        if not room_2p:
            log.info("[%s] 2名 room not found in day-31 cell", self.name)
            return False

        room_div = room_2p.find_parent(class_="room-daily")
        if not room_div:
            return False

        status_el = room_div.find(class_="room-status")
        if not status_el:
            return False

        classes = status_el.get("class", [])
        status_text = status_el.get_text(strip=True)
        log.info("[%s] Day 31 / 2名 status: '%s' (class=%s)", self.name, status_text, classes)

        return "full" not in classes
