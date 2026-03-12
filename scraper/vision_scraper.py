#!/usr/bin/env python3
"""
Vision.com.tw 班表爬蟲 - 適用於展望亞洲科技 (vision.com.tw) 系統
功能：
1. 對指定 vision.com.tw 診所發 POST 請求取得週班表 HTML
2. 解析 myFunction() 呼叫，提取醫師 / 日期 / 時段
3. 套用 whitelist 過濾，輸出 schedules.json sessions 格式

目前支援診所：
  c24 新店精睿泌尿科 → https://14387.vision.com.tw/Register
    whitelist: [黃旭澤]

用法：
  # 爬取 c24 當週 + 未來 4 週班表，列印 sessions
  python3 vision_scraper.py --clinic c24

  # 輸出 JSON（可直接貼入 schedules.json）
  python3 vision_scraper.py --clinic c24 --output sessions.json

  # 爬取指定起始日
  python3 vision_scraper.py --clinic c24 --start-date 2026-04-06

  # 爬取多週（預設 5 週）
  python3 vision_scraper.py --clinic c24 --weeks 8
"""

import argparse
import json
import re
import ssl
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

# 部分 vision.com.tw 站台 SSL 憑證鏈不完整，跳過驗證
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

SCRAPER_DIR = Path(__file__).parent
SCHEDULES_JSON = SCRAPER_DIR.parent / "schedules.json"

# vision.com.tw 診所設定
VISION_CLINICS = {
    "c24": {
        "name": "新店精睿泌尿科",
        "aliases": ["新店精睿"],
        "abbrev": "jr",  # session ID 前綴
        "base_url": "https://14387.vision.com.tw/Register",
    }
}

SLOT_MAP = {
    "上午門診": ("morning",   "早診 09:00–12:00"),
    "下午門診": ("afternoon", "午診 14:00–17:00"),
    "晚上門診": ("evening",   "晚診 18:00–20:30"),
}

SLOT_CHAR = {"morning": "m", "afternoon": "a", "evening": "e"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://14387.vision.com.tw/Register",
}


def fetch_week_html(base_url: str, date_str: str) -> str:
    """POST /Register 取得指定週 HTML"""
    body = urllib.parse.urlencode({"date": date_str, "type": 1}).encode()
    req = urllib.request.Request(base_url, data=body, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_sessions(html: str, clinic_id: str, abbrev: str, whitelist: list) -> list:
    """解析 myFunction() 呼叫，回傳 session list"""
    # myFunction('第一診', '黃旭澤', '103', 'uuid', '泌尿科', '2026-03-16', '週一', '上午門診', '09:00~12:00', 0, '-1', 'onclick')
    pattern = re.compile(
        r"myFunction\("
        r"'[^']*',\s*"        # room
        r"'([^']+)',\s*"      # doctor_name
        r"'[^']*',\s*"        # doctor_code
        r"'[^']*',\s*"        # doctor_id (uuid)
        r"'[^']*',\s*"        # subject
        r"'(\d{4}-\d{2}-\d{2})',\s*"  # date
        r"'[^']*',\s*"        # week (週四 etc.)
        r"'([^']+)',\s*"      # time_text (上午門診 etc.)
    )

    sessions = []
    seen_ids = set()

    for m in pattern.finditer(html):
        doctor_name = m.group(1)
        date = m.group(2)
        time_text = m.group(3)

        # whitelist 過濾
        if whitelist and doctor_name not in whitelist:
            continue

        slot_info = SLOT_MAP.get(time_text)
        if not slot_info:
            continue
        slot, time_label = slot_info

        mmdd = date[5:].replace("-", "")
        base_id = f"{abbrev}_{SLOT_CHAR[slot]}_{mmdd}"

        # 同一 id 有多位醫師時加後綴
        session_id = base_id
        suffix = 2
        while session_id in seen_ids:
            session_id = f"{base_id}_{suffix}"
            suffix += 1
        seen_ids.add(session_id)

        sessions.append({
            "id": session_id,
            "doctor_name": doctor_name,
            "clinic_id": clinic_id,
            "date": date,
            "slot": slot,
            "time_label": time_label,
            "source_note": f"vision.com.tw 官網班表 {datetime.now().strftime('%Y-%m-%d')} 更新",
        })

    return sessions


def get_monday(date: datetime) -> datetime:
    """取得該週週一"""
    return date - timedelta(days=date.weekday())


def scrape_clinic(clinic_id: str, start_date: datetime = None, weeks: int = 5) -> list:
    """爬取指定診所未來 N 週班表"""
    config = VISION_CLINICS.get(clinic_id)
    if not config:
        raise ValueError(f"未知診所 ID: {clinic_id}")

    # 載入 whitelist
    with open(SCHEDULES_JSON, encoding="utf-8") as f:
        sched = json.load(f)
    clinic_cfg = next((c for c in sched["clinics"] if c["id"] == clinic_id), {})
    whitelist = clinic_cfg.get("whitelist", [])

    if start_date is None:
        start_date = datetime.now()

    all_sessions = []
    seen_session_ids = set()

    # 每次查詢：從上週一開始，往後 weeks 週（系統返回下週資料）
    # 所以 query_monday = target_week_monday - 7 days
    target_monday = get_monday(start_date)

    for week_offset in range(weeks):
        query_date = target_monday + timedelta(weeks=week_offset) - timedelta(weeks=1)
        date_str = query_date.strftime("%Y-%m-%d")

        print(f"  📅 查詢 {config['name']} date={date_str}（目標週：{(query_date + timedelta(weeks=1)).strftime('%Y-%m-%d')} 起）...")

        try:
            html = fetch_week_html(config["base_url"], date_str)
            sessions = parse_sessions(html, clinic_id, config["abbrev"], whitelist)

            # 去重
            new_sessions = [s for s in sessions if s["id"] not in seen_session_ids]
            seen_session_ids.update(s["id"] for s in new_sessions)
            all_sessions.extend(new_sessions)

            print(f"    → 找到 {len(new_sessions)} 筆（{whitelist} 過濾後）")
            time.sleep(1)

        except Exception as e:
            print(f"  ❌ 爬取失敗: {e}")

    return all_sessions


def main():
    parser = argparse.ArgumentParser(description="Vision.com.tw 班表爬蟲")
    parser.add_argument("--clinic", required=True, help="診所 ID，例如 c24")
    parser.add_argument("--weeks", type=int, default=5, help="爬取週數（預設 5）")
    parser.add_argument("--start-date", help="起始日期 YYYY-MM-DD（預設今天）")
    parser.add_argument("--output", help="輸出 JSON 檔案路徑")
    args = parser.parse_args()

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date else datetime.now()

    print(f"\n🕷️  Vision.com.tw 爬蟲 - {args.clinic}")
    print(f"   起始日: {start_date.strftime('%Y-%m-%d')}, 爬取 {args.weeks} 週\n")

    sessions = scrape_clinic(args.clinic, start_date, args.weeks)

    print(f"\n✅ 共 {len(sessions)} 筆 sessions")
    for s in sessions:
        print(f"  {s['id']:20} {s['date']} {s['slot']:10} {s['doctor_name']}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
        print(f"\n📄 已輸出到 {args.output}")
    else:
        print("\n💡 加上 --output sessions.json 可直接輸出 JSON")


if __name__ == "__main__":
    main()
