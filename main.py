import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import dotenv_values

from checkers.yamatan import YamatanChecker
from checkers.tomoekan import TomoekanChecker
from checkers.goraikoukan import GoraikoukanChecker
from notifier import send_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

CHECK_INTERVAL = 60         # seconds, for local loop mode
NOTIFY_COOLDOWN_HOURS = 1   # hours between repeat emails in --once mode
STATE_FILE = "state.json"


def load_config():
    config = dict(dotenv_values(".env"))
    # Environment variables override .env (used by GitHub Actions)
    for key in ("GMAIL_USER", "GMAIL_APP_PASSWORD", "NOTIFY_EMAIL",
                "TARGET_DATE", "TARGET_PEOPLE", "DEBUG"):
        if os.environ.get(key):
            config[key] = os.environ[key]
    return config


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def cooldown_passed(state: dict, name: str) -> bool:
    last = state.get(name, {}).get("last_notified")
    if not last:
        return True
    return datetime.now() - datetime.fromisoformat(last) > timedelta(hours=NOTIFY_COOLDOWN_HOURS)


def check_all(config: dict, checkers: list, state: dict):
    """Run one check cycle across all sites, mutating state in place."""
    for checker in checkers:
        try:
            available = checker.check()
            if available:
                log.info("[%s] AVAILABLE!", checker.name)
                if cooldown_passed(state, checker.name):
                    send_notification(checker.name, checker.url, config)
                    state[checker.name] = {"last_notified": datetime.now().isoformat()}
                else:
                    log.info("[%s] Skipping email (sent < %dh ago)", checker.name, NOTIFY_COOLDOWN_HOURS)
            else:
                log.info("[%s] Not available yet.", checker.name)
                state.pop(checker.name, None)
        except Exception as e:
            log.error("[%s] Error: %s", checker.name, e)


def run_once(config: dict, checkers: list):
    """Check all sites once and exit."""
    state = load_state()
    check_all(config, checkers, state)
    save_state(state)


def run_duration(config: dict, checkers: list, duration: int):
    """Check every 60 seconds for `duration` seconds, then exit.

    Used by GitHub Actions to achieve ~1-minute polling within a
    5-minute cron window (e.g. --duration 240 → 4 checks/job × 5-min cron).
    """
    deadline = datetime.now() + timedelta(seconds=duration)
    iteration = 0
    while datetime.now() < deadline:
        iteration += 1
        log.info("=== Check #%d (deadline in %ds) ===",
                 iteration, (deadline - datetime.now()).seconds)
        state = load_state()
        check_all(config, checkers, state)
        save_state(state)
        remaining = (deadline - datetime.now()).total_seconds()
        if remaining > CHECK_INTERVAL:
            log.info("Next check in %ds.", CHECK_INTERVAL)
            time.sleep(CHECK_INTERVAL)
        else:
            break  # not enough time for another full cycle


def run_loop(config: dict, checkers: list):
    """Continuous loop mode for local use."""
    notified = {c.name: False for c in checkers}
    log.info("Monitor started. Checking every %d seconds.", CHECK_INTERVAL)
    log.info("Target: July %s, %s people", config.get("TARGET_DATE", "31"), config.get("TARGET_PEOPLE", "2"))

    while True:
        log.info("=== Check at %s ===", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        for checker in checkers:
            try:
                available = checker.check()
                if available:
                    log.info("[%s] AVAILABLE!", checker.name)
                    if not notified[checker.name]:
                        send_notification(checker.name, checker.url, config)
                        notified[checker.name] = True
                else:
                    log.info("[%s] Not available yet.", checker.name)
                    notified[checker.name] = False
            except Exception as e:
                log.error("[%s] Error: %s", checker.name, e)

        log.info("Next check in %d seconds.", CHECK_INTERVAL)
        time.sleep(CHECK_INTERVAL)


def main():
    parser = argparse.ArgumentParser(description="Fuji mountain hut availability monitor")
    parser.add_argument("--once", action="store_true",
                        help="Run checks once and exit")
    parser.add_argument("--duration", type=int, default=0,
                        help="Run checks every 60s for this many seconds, then exit (used by GitHub Actions)")
    args = parser.parse_args()

    config = load_config()
    if not config.get("GMAIL_USER") or not config.get("GMAIL_APP_PASSWORD"):
        log.error("Missing GMAIL_USER or GMAIL_APP_PASSWORD — set them in .env or environment variables.")
        sys.exit(1)

    checkers = [
        YamatanChecker(config),
        TomoekanChecker(config),
        GoraikoukanChecker(config),
    ]

    if args.once:
        run_once(config, checkers)
    elif args.duration > 0:
        run_duration(config, checkers, args.duration)
    else:
        run_loop(config, checkers)


if __name__ == "__main__":
    main()
