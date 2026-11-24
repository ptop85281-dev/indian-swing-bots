import os
import re
import json
import requests
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
STATE_FILE = "seen_orders.json"

IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime.now(IST)
TODAY_BSE = NOW.strftime("%Y%m%d")
TODAY_NSE = NOW.strftime("%d-%m-%Y")

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
        json.dump(list(seen_ids)[-800:], f)


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=15,
    )


def fetch_bse():
    url = (
        f"https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
        f"?pageno=1&strCat=-1&strPrevDate={TODAY_BSE}&strScrip=&strSearch=P&strToDate={TODAY_BSE}&strType=C&subcategory=-1"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bseindia.com/",
        "Accept": "application/json",
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        items = []
        for row in r.json().get("Table", []):
            pdf = row.get("ATTACHMENTNAME", "")
            items.append({
                "id": f"BSE_{row.get('NEWSID', '')}",
                "company": row.get("SLONGNAME", "Unknown"),
                "symbol": str(row.get("SCRIP_CD", "")),
                "text": f"{row.get('HEADLINE', '')} {row.get('MORE', '')}",
                "link": f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{pdf}" if pdf else "",
            })
        return items
    except Exception:
        return []


def fetch_nse():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
    }
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&from_date={TODAY_NSE}&to_date={TODAY_NSE}"
        r = session.get(url, headers=headers, timeout=15)
        items = []
        for row in r.json():
            seq = row.get("seq_id") or row.get("an_dt", "")
            items.append({
                "id": f"NSE_{row.get('symbol', '')}_{seq}",
                "company": row.get("sm_name", "Unknown"),
                "symbol": row.get("symbol", ""),
                "text": f"{row.get('desc', '')} {row.get('attchmntText', '')}",
                "link": row.get("attchmntFile", ""),
            })
        return items
    except Exception:
        return []


def main():
    seen = load_seen()
    new_seen = set(seen)
    all_items = fetch_bse() + fetch_nse()

    for item in all_items:
        uid = item["id"]
        if not uid or uid in seen:
            continue
        if KEYWORDS.search(item["text"]):
            val_match = VALUE_PATTERN.search(item["text"])
            order_val = f"₹{val_match.group(1)} {val_match.group(2)}" if val_match else "Check PDF"
            msg = (
                f"🚨 <b>ORDER ALERT: {item['company']}</b> ({item['symbol']})\n"
                f"💰 <b>Est. Value:</b> {order_val}\n"
                f"📰 <b>Details:</b> {item['text'][:220]}\n"
            )
            if item["link"]:
                msg += f"📄 <a href='{item['link']}'>Open Filing PDF</a>"
            send_telegram(msg)
        new_seen.add(uid)

    save_seen(new_seen)


if __name__ == "__main__":
    main()
