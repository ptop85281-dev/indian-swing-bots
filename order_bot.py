import os
import re
import json
import requests
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
STATE_FILE = "seen_orders.json"

IST = timezone(timedelta(hours=5, minutes=30))
TODAY = datetime.now(IST).strftime("%Y%m%d")

KEYWORDS = re.compile(
    r"\b(order|orders|contract|contracts|loa|letter of award|work order|awarded|bagged)\b",
    re.IGNORECASE,
)
VALUE_PATTERN = re.compile(
    r"(?:rs\.?|inr|₹)\s*([\d,]+(?:\.\d+)?)\s*(crore|crores|cr|lakh|lakhs)",
    re.IGNORECASE,
)


def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen_ids):
    with open(STATE_FILE, "w") as f:
        json.dump(list(seen_ids)[-500:], f)


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=15,
    )


def fetch_bse_orders():
    url = (
        f"https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
        f"?pageno=1&strCat=-1&strPrevDate={TODAY}&strScrip=&strSearch=P&strToDate={TODAY}&strType=C&subcategory=-1"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bseindia.com/",
        "Accept": "application/json",
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json().get("Table", [])


def main():
    seen = load_seen()
    rows = fetch_bse_orders()
    new_seen = set(seen)

    for row in rows:
        news_id = str(row.get("NEWSID", ""))
        if not news_id or news_id in seen:
            continue

        headline = row.get("HEADLINE", "") or ""
        more = row.get("MORE", "") or ""
        combined = f"{headline} {more}"

        if KEYWORDS.search(combined):
            company = row.get("SLONGNAME", "Unknown")
            scrip = row.get("SCRIP_CD", "")
            pdf_name = row.get("ATTACHMENTNAME", "")
            pdf_link = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{pdf_name}" if pdf_name else ""

            val_match = VALUE_PATTERN.search(combined)
            order_val = f"₹{val_match.group(1)} {val_match.group(2)}" if val_match else "Check PDF"

            msg = (
                f"🚨 <b>ORDER ALERT: {company}</b> ({scrip})\n"
                f"💰 <b>Est. Value:</b> {order_val}\n"
                f"📰 <b>Headline:</b> {headline[:220]}\n"
            )
            if pdf_link:
                msg += f"📄 <a href='{pdf_link}'>Open BSE PDF</a>"

            send_telegram(msg)

        new_seen.add(news_id)

    save_seen(new_seen)


if __name__ == "__main__":
    main()
