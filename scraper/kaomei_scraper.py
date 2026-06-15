#!/usr/bin/env python3
"""
新店高美泌尿科官網月班表爬蟲。

來源目前是靜態 HTML 表格：
  https://www.kaomei.com.tw/hours.asp?id=37

解析策略刻意避開 inline style / line number，改用表格內容特徵：
  - header row 包含 MON..SUN
  - slot rows 第一欄為 上午 / 下午 / 晚上
  - 第二欄為時間，後七欄為週一至週日醫師
"""

import argparse
import calendar
import json
import re
import urllib.request
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path


CLINIC_ID = "c26"
CLINIC_NAME = "新店高美泌尿科"
SOURCE_URL = "https://www.kaomei.com.tw/hours.asp?id=37"
ABBREV = "km"
SCHEDULES_JSON = Path(__file__).resolve().parent.parent / "schedules.json"

DAY_KEYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
DAY_INDEX = {key: idx for idx, key in enumerate(DAY_KEYS)}
SLOT_MAP = {
    "上午": ("morning", "m", "早診"),
    "下午": ("afternoon", "a", "午診"),
    "晚上": ("evening", "e", "晚診"),
}


class TableParser(HTMLParser):
    """Small stdlib table extractor; enough for the static Kaomei schedule."""

    def __init__(self):
        super().__init__()
        self.tables = []
        self._table = None
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._table = []
        elif self._table is not None and tag == "tr":
            self._row = []
        elif self._row is not None and tag in ("td", "th"):
            self._cell = []

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            text = "".join(self._cell).replace("\xa0", " ")
            text = " ".join(text.split())
            self._row.append(text)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None


def fetch_html(url: str = SOURCE_URL) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def find_schedule_table(html: str) -> list[list[str]]:
    parser = TableParser()
    parser.feed(html)
    for table in parser.tables:
        flat = " ".join(" ".join(row) for row in table)
        has_days = all(day in flat for day in DAY_KEYS)
        has_slots = all(slot in flat for slot in SLOT_MAP)
        if has_days and has_slots:
            return table
    raise ValueError("找不到高美門診表格：缺 MON~SUN 或 上午/下午/晚上列")


def normalize_time(raw: str) -> str:
    times = re.findall(r"\d{1,2}:\d{2}", raw)
    if len(times) >= 2:
        return f"{times[0]}–{times[1]}"
    return raw.replace("|", "–").strip()


def extract_doctors(raw: str) -> list[str]:
    text = raw.strip()
    if not text:
        return []
    parts = re.split(r"[、，,;/／]+", text)
    return [p.strip() for p in parts if p.strip()]


def parse_weekly_schedule(html: str) -> list[dict]:
    table = find_schedule_table(html)
    header = table[0]
    if len(header) == 8 and header[0] == "":
        header = ["", *header]
    if len(header) < 9 or header[2:9] != DAY_KEYS:
        raise ValueError(f"高美門診表 header 結構異常：{table[0]}")

    weekly = []
    for row in table[1:]:
        if len(row) < 9:
            continue
        label = row[0]
        if label not in SLOT_MAP:
            continue
        slot, slot_char, label_prefix = SLOT_MAP[label]
        time_range = normalize_time(row[1])
        time_label = f"{label_prefix} {time_range}"
        for day_key, cell in zip(DAY_KEYS, row[2:9]):
            for doctor in extract_doctors(cell):
                weekly.append(
                    {
                        "weekday": DAY_INDEX[day_key],
                        "day_key": day_key,
                        "slot": slot,
                        "slot_char": slot_char,
                        "doctor_name": doctor,
                        "time_label": time_label,
                    }
                )
    if not weekly:
        raise ValueError("高美門診表解析結果為空")
    return weekly


def month_end(d: date, months: int) -> date:
    year = d.year
    month = d.month + months - 1
    year += (month - 1) // 12
    month = ((month - 1) % 12) + 1
    return date(year, month, calendar.monthrange(year, month)[1])


def daterange(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def generate_sessions(weekly: list[dict], start: date, end: date) -> list[dict]:
    by_weekday = {}
    for entry in weekly:
        by_weekday.setdefault(entry["weekday"], []).append(entry)

    sessions = []
    update_date = datetime.now().strftime("%Y-%m-%d")
    for current in daterange(start, end):
        entries = by_weekday.get(current.weekday(), [])
        seen_base_ids = {}
        for entry in entries:
            mmdd = current.strftime("%m%d")
            base_id = f"{ABBREV}_{entry['slot_char']}_{mmdd}"
            seen_base_ids[base_id] = seen_base_ids.get(base_id, 0) + 1
            suffix = "" if seen_base_ids[base_id] == 1 else f"_{seen_base_ids[base_id]}"
            sessions.append(
                {
                    "id": f"{base_id}{suffix}",
                    "doctor_name": entry["doctor_name"],
                    "clinic_id": CLINIC_ID,
                    "date": current.isoformat(),
                    "slot": entry["slot"],
                    "time_label": entry["time_label"],
                    "source_note": f"新店高美官網月班表 {update_date} 更新",
                }
            )
    return sessions


def load_or_fetch_html(args) -> str:
    if args.input:
        return Path(args.input).read_text(encoding="utf-8", errors="replace")
    return fetch_html()


def update_schedules(sessions: list[dict], start: date, end: date) -> None:
    with SCHEDULES_JSON.open(encoding="utf-8") as f:
        data = json.load(f)

    if not any(c["id"] == CLINIC_ID for c in data["clinics"]):
        data["clinics"].append(
            {
                "id": CLINIC_ID,
                "name": CLINIC_NAME,
                "aliases": ["新店高美"],
                "color": "#16a085",
                "source_url": SOURCE_URL,
                "schedule_type": "C1",
                "whitelist": [],
                "blacklist": [],
            }
        )

    before = len(data["sessions"])
    data["sessions"] = [
        s
        for s in data["sessions"]
        if not (s.get("clinic_id") == CLINIC_ID and start.isoformat() <= s.get("date", "") <= end.isoformat())
    ]
    removed = before - len(data["sessions"])
    data["sessions"].extend(sessions)
    data["meta"]["generated_at"] = datetime.now().isoformat(timespec="seconds")

    with SCHEDULES_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"updated schedules.json: removed={removed} added={len(sessions)} total={len(data['sessions'])}")


def main():
    parser = argparse.ArgumentParser(description="新店高美泌尿科官網月班表爬蟲")
    parser.add_argument("--input", help="使用已下載 HTML，不重新抓官網")
    parser.add_argument("--start-date", default=datetime.now().strftime("%Y-%m-%d"), help="開始日期 YYYY-MM-DD")
    parser.add_argument("--end-date", help="結束日期 YYYY-MM-DD")
    parser.add_argument("--months", type=int, default=2, help="未指定 --end-date 時，產生到第 N 個月份月底")
    parser.add_argument("--output", help="輸出 sessions JSON")
    parser.add_argument("--update-schedules", action="store_true", help="寫入 schedules.json")
    parser.add_argument("--print-weekly", action="store_true", help="列印解析出的週班表")
    args = parser.parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end = datetime.strptime(args.end_date, "%Y-%m-%d").date() if args.end_date else month_end(start, args.months)
    if end < start:
        raise SystemExit("--end-date 不可早於 --start-date")

    html = load_or_fetch_html(args)
    weekly = parse_weekly_schedule(html)
    sessions = generate_sessions(weekly, start, end)

    if args.print_weekly:
        for entry in weekly:
            print(f"{entry['day_key']} {entry['slot']:<9} {entry['time_label']} {entry['doctor_name']}")
    print(f"parsed weekly_entries={len(weekly)} sessions={len(sessions)} range={start}..{end}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"wrote {args.output}")

    if args.update_schedules:
        update_schedules(sessions, start, end)


if __name__ == "__main__":
    main()
