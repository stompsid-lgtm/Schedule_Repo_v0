#!/usr/bin/env python3
"""
hixcare 班表爬蟲 — hixcare SaaS 線上掛號系統（Vue SPA + REST API）

直接 POST 後端 REST API 取得結構化班表 JSON，不需開瀏覽器、不需 OCR。
適用診所見下方 HIXCARE_CLINICS。

API（base 為各診所 hixcare 子網域，例 https://fcbone-schedule.hixcare.tw）：
  1. 診所設定：GET  {base}/hixLocal/sysConfig/getHixConfig
       → result 含 HOSPITAL_ID / HOSPITAL_NAME / SCHEDULE_DEFAULT_DIVISION(科別) 等
  2. 班表查詢：POST {base}/hixLocal/regSchedule/find
       body: {"dateFrom":"YYYY-MM-DD","dateTo":"YYYY-MM-DD","flagType":"1"}
       header: Content-Type: application/json
       → result[] 每筆班表，欄位見 _session_from_record()

如何替新診所找出 API（未來若有別家也搬 hixcare）：
  1. curl 診所掛號頁，會看到 <script src="/assets/index-*.js">（Vue SPA bundle）
  2. 抓該 bundle，grep 出 baseURL（通常 `${host}/hixLocal`）與 code-split chunk
     （班表頁是 assets/ScheduleView-*.js）
  3. 抓 ScheduleView chunk，grep `.post("/regSchedule/find"` 與其 payload
  → 之後把診所加進下方 HIXCARE_CLINICS 即可重用本腳本

目前支援診所：
  c03 富新骨科 → https://fcbone-schedule.hixcare.tw/schedule

用法：
  # 抓 c03 本週班表，列印（不寫回）
  python3 hixcare_scraper.py --clinic c03

  # 抓本週 + 未來共 2 週
  python3 hixcare_scraper.py --clinic c03 --weeks 2

  # 指定日期範圍
  python3 hixcare_scraper.py --clinic c03 --date-from 2026-06-29 --date-to 2026-07-05

  # 輸出 sessions JSON 到檔案
  python3 hixcare_scraper.py --clinic c03 --output /tmp/c03.json

  # 直接寫回 schedules.json（刪該診所該範圍舊 sessions、補入新的、更新 generated_at）
  python3 hixcare_scraper.py --clinic c03 --update-schedules
"""

import argparse
import json
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

SCRAPER_DIR = Path(__file__).parent
SCHEDULES_JSON = SCRAPER_DIR.parent / "schedules.json"

# hixcare 診所設定。未來有別家搬 hixcare，照樣加一筆即可。
HIXCARE_CLINICS = {
    "c03": {
        "name": "富新骨科",
        "aliases": ["富新"],
        "abbrev": "fc",                       # session ID 前綴（沿用舊 CXMS 代碼）
        "base_url": "https://fcbone-schedule.hixcare.tw",
        "exclude_rooms": ["成人健檢"],         # 非骨科門診的診間，不收
    }
}

# refShiftId → (slot, ID 簡碼, time_label 中文前綴)
SLOT_MAP = {
    "AM":      ("morning",   "m", "上午"),
    "PM":      ("afternoon", "a", "下午"),
    "EVENING": ("evening",   "e", "晚上"),
}

# hixClinicRoomName → 診次（用於 ID 與 source_note）
ROOM_SEQ = {"一診": "1", "二診": "2"}


def _http_json(url, payload=None, timeout=15):
    """發 GET（payload=None）或 POST（payload=dict）並回傳解析後的 JSON。"""
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_hix_config(base_url):
    """取得診所系統設定（含 HOSPITAL_ID / 科別等）。"""
    res = _http_json(f"{base_url}/hixLocal/sysConfig/getHixConfig")
    return res.get("result", {}) if res.get("code") == 0 else {}


def fetch_schedule(base_url, date_from, date_to):
    """POST 取得 date_from~date_to 的班表 raw records。"""
    res = _http_json(f"{base_url}/hixLocal/regSchedule/find",
                     payload={"dateFrom": date_from, "dateTo": date_to, "flagType": "1"})
    if res.get("code") != 0:
        raise RuntimeError(f"regSchedule/find 回傳非 0：{res.get('code')} / {res.get('msg')}")
    return res.get("result", [])


def _session_from_record(rec, abbrev):
    """把一筆 hixcare 班表 record 轉成 schedules.json session 物件；無效回 None。"""
    shift = SLOT_MAP.get(rec.get("refShiftId"))
    if not shift:
        return None
    slot, scode, prefix = shift
    room = rec.get("hixClinicRoomName", "")
    doctor = rec.get("doctorName", "")
    date = rec.get("schDate", "")[:10]          # "2026-06-29T00:00:00.000Z" → "2026-06-29"
    if not (date and doctor):
        return None
    seq = ROOM_SEQ.get(room, "1")
    mmdd = date[5:7] + date[8:10]
    start = (rec.get("startTime") or "")[:5]
    end = (rec.get("endTime") or "")[:5]
    time_label = f"{prefix} {start}–{end}" if start and end else prefix
    return {
        "id": f"{abbrev}_{scode}{seq}_{mmdd}",
        "doctor_name": doctor,
        "clinic_id": None,                       # 由 caller 填入
        "date": date,
        "slot": slot,
        "time_label": time_label,
        "source_note": f"{prefix}{room}",
    }


def build_sessions(clinic_id, date_from, date_to):
    """抓取並轉成 sessions list（已套用排除規則）。"""
    cfg = HIXCARE_CLINICS[clinic_id]
    records = fetch_schedule(cfg["base_url"], date_from, date_to)
    exclude_rooms = set(cfg.get("exclude_rooms", []))
    sessions = []
    skipped = 0
    for rec in records:
        room = rec.get("hixClinicRoomName", "")
        doctor = rec.get("doctorName", "")
        # 排除：指定診間（如成人健檢）、健檢時段（doctorName 等於診間名）、停診(flagOpenClose=9)
        if room in exclude_rooms or doctor in exclude_rooms or doctor == room:
            skipped += 1
            continue
        if rec.get("flagOpenClose") == "9":
            skipped += 1
            continue
        s = _session_from_record(rec, cfg["abbrev"])
        if s is None:
            skipped += 1
            continue
        s["clinic_id"] = clinic_id
        sessions.append(s)
    return sessions, skipped


def week_range(start_date, weeks):
    """回傳 (date_from, date_to)：start_date 所在週的週一 ~ 第 weeks 週的週日。"""
    monday = start_date - timedelta(days=start_date.weekday())
    sunday = monday + timedelta(days=7 * weeks - 1)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


def update_schedules_json(clinic_id, sessions, date_from, date_to):
    """寫回 schedules.json：刪該診所 [date_from, date_to] 舊 sessions、補入新的。不可變寫法。"""
    with open(SCHEDULES_JSON, encoding="utf-8") as f:
        data = json.load(f)
    kept = [s for s in data["sessions"]
            if not (s["clinic_id"] == clinic_id and date_from <= s["date"] <= date_to)]
    removed = len(data["sessions"]) - len(kept)
    new_data = dict(
        data,
        sessions=kept + sessions,
        meta=dict(data["meta"], generated_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
    )
    with open(SCHEDULES_JSON, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    return removed


def main():
    ap = argparse.ArgumentParser(description="hixcare 班表爬蟲")
    ap.add_argument("--clinic", required=True, choices=sorted(HIXCARE_CLINICS),
                    help="診所代碼，例 c03")
    ap.add_argument("--weeks", type=int, default=1, help="從起始週起算幾週（預設 1=本週）")
    ap.add_argument("--start-date", help="起始日 YYYY-MM-DD（預設今天）")
    ap.add_argument("--date-from", help="明確起日 YYYY-MM-DD（覆寫 weeks/start-date）")
    ap.add_argument("--date-to", help="明確迄日 YYYY-MM-DD（覆寫 weeks/start-date）")
    ap.add_argument("--output", help="輸出 sessions JSON 到檔案")
    ap.add_argument("--update-schedules", action="store_true",
                    help="直接寫回 schedules.json")
    args = ap.parse_args()

    if args.date_from and args.date_to:
        date_from, date_to = args.date_from, args.date_to
    else:
        start = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date else datetime.now()
        date_from, date_to = week_range(start, args.weeks)

    cfg = HIXCARE_CLINICS[args.clinic]
    print(f"診所：{args.clinic} {cfg['name']}　範圍：{date_from} ~ {date_to}")

    sessions, skipped = build_sessions(args.clinic, date_from, date_to)
    by_date = {}
    for s in sessions:
        by_date.setdefault(s["date"], []).append(s)
    for d in sorted(by_date):
        for s in sorted(by_date[d], key=lambda x: x["id"]):
            print(f"  {d} {s['source_note']:<6} {s['doctor_name']:<5} {s['time_label']}")
    print(f"\n共 {len(sessions)} 筆門診，跳過 {skipped} 筆（健檢/停診/無效）")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
        print(f"已輸出 → {args.output}")

    if args.update_schedules:
        removed = update_schedules_json(args.clinic, sessions, date_from, date_to)
        print(f"✅ 已寫回 schedules.json（刪舊 {removed} / 新增 {len(sessions)}）")


if __name__ == "__main__":
    main()
