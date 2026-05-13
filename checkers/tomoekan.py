import logging
from playwright.sync_api import Page
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


class TomoekanChecker(BaseChecker):
    name = "巴館 (Tomoekan)"
    url = URL

    def _is_available(self, page: Page) -> bool:
        try:
            page.wait_for_selector("td[class*='day-31']", timeout=10000)
        except Exception:
            log.warning(f"[{self.name}] Timed out waiting for day-31 cell")
            return False

        # Find the day-31 cell
        day31_cell = page.query_selector("td[class*='day-31']")
        if not day31_cell:
            log.info(f"[{self.name}] Day 31 cell not found in calendar")
            return False

        # Find the 2-person room within that cell
        room_2p = day31_cell.query_selector(f".{ROOM_2P_CLASS}")
        if not room_2p:
            log.info(f"[{self.name}] 2名 room not found in day-31 cell")
            return False

        # The room-daily div wrapping this span
        room_div = room_2p.evaluate_handle("el => el.closest('.room-daily')").as_element()
        if not room_div:
            log.info(f"[{self.name}] Could not find room-daily wrapper")
            return False

        status_el = room_div.query_selector(".room-status")
        if not status_el:
            log.info(f"[{self.name}] No room-status element found")
            return False

        classes = status_el.get_attribute("class") or ""
        status_text = (status_el.inner_text() or "").strip()
        log.info(f"[{self.name}] Day 31 / 2名 status: '{status_text}' (class='{classes}')")

        # "full" class means unavailable
        if "full" in classes:
            return False

        # No "full" class = available (shows 〇 or a remaining count)
        return True
