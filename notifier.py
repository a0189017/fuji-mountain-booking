import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger(__name__)


def send_notification(site_name: str, url: str, config: dict):
    gmail_user = config["GMAIL_USER"]
    gmail_password = config["GMAIL_APP_PASSWORD"]
    notify_email = config["NOTIFY_EMAIL"]
    target_date = config.get("TARGET_DATE", "31")
    target_people = config.get("TARGET_PEOPLE", "2")

    subject = f"[富士山預約] {site_name} 7/{target_date} 有空位！"
    body = f"""\
{site_name} 在 7/{target_date} 出現可供 {target_people} 人預約的空位！

請立即前往預約：
{url}

---
此訊息由自動監控程式發送
"""

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = notify_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, notify_email, msg.as_string())
        log.info(f"Notification sent to {notify_email} for {site_name}")
    except Exception as e:
        log.error(f"Failed to send email: {e}")
        raise


if __name__ == "__main__":
    import os
    from dotenv import dotenv_values
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    config = dotenv_values(".env")
    send_notification("測試網站", "https://example.com", config)
    print("Test email sent.")
