# scraper（Schedule_Repo_v0）| lang:zh-TW | for-AI-parsing | optimize=compliance

<meta>
repo: stompsid-lgtm/Schedule_Repo_v0（private）
purpose: 半自動化診所排班資料管理系統（26 家診所 → schedules.json → index.html PWA）
</meta>

<docs label="子文件索引 | 各主題權威在子文件">
SOP.md → 25 家診所更新 SOP（類型分類、操作步驟、衝突檢查、每週/月執行清單）
Spec.md → PWA 前端規格（使用者流程、技術限制、JSON schema、開發要求）
Log.md → 歷史開發日誌（資料修正紀錄、UI 更新、bug fix）
scraper/ocr_corrections.md → OCR 易誤辨醫師名字對照表
</docs>

<conn label="精確保留 | 禁壓縮">

DIRECTORY:
  ```
  scraper/                             # Git root
  ├── index.html                       # 診所排班 PWA 前端
  ├── schedules.json                   # 核心資料檔（所有診所排班）
  ├── schedules.json.backup            # 備份
  ├── CLAUDE.md                        # 本檔（SOT 索引）
  ├── SOP.md                           # 更新 SOP（v1.8）
  ├── Spec.md                          # PWA 規格
  ├── Log.md                           # 開發日誌
  └── scraper/
      ├── web_validator.py             # CXMS 網站爬取與快照
      ├── fb_snapshot.py               # Facebook/LINE VOOM 截圖
      ├── image_validator.py           # 靜態圖片診所驗證管理
      ├── kaomei_scraper.py            # 新店高美官網月班表爬蟲（c26）
      ├── vision_scraper.py            # Vision.com.tw 班表爬蟲（c24）
      ├── hixcare_scraper.py           # hixcare 線上系統班表爬蟲（c03 富新，POST API）
      ├── extend_fixed.py             # 每月初延伸固定班表 sessions
      ├── weili_scraper.py             # 維力骨科 Selenium 爬蟲（保留備用）
      ├── ocr_corrections.md           # OCR 修正對照表
      └── snapshots/                   # 各診所快照（web/social/image，已 gitignore）
  ```

</conn>

<clinic-types label="快速路由 | 詳細步驟見 SOP.md">

| 類型 | 班表性質 | 頻率 | 診所 | 工具/方法 |
|------|---------|------|------|----------|
| A（CXMS） | 週班 | 每週日 | c02 維恩、c04 得安、c05 昌惟、c06 昌禾、c07 杏光、c19 得揚、c20 力康、c25 上禾 | curl HTTP → Python 解析 |
| A-hix（hixcare） | 週班 | 每週日 | c03 富新 | hixcare_scraper.py（POST REST API） |
| B1（FB 月班） | 月班 | 月底 | c09 健維、c17 仁祐、c22 順安、c23 黃石 | 截圖 → 人工轉錄 |
| B2（FB 固定） | 固定 | 月初延伸 | c01 禾安、c12 陳正傑 | extend_fixed.py |
| C1（官網月） | 月班 | 月底 | c15 誠陽、c16 康澤、c26 新店高美 | c15/c16 截圖 → 人工轉錄；c26 curl HTML → parser |
| C2（官網週） | 週班 | 每週日 | c21 永馨 | POST API → 解析 |
| C3（官網固定） | 固定 | 月初確認+手動延伸 | c10 板橋維力、c11 土城維力、c18 祥明 | curl 確認 → Python 手動生成 |
| D（靜態圖片） | 固定 | 月初延伸 / 半年確認 | c08 正陽、c13 悅滿意永和、c14 悅滿意新店 | extend_fixed.py |
| E（Vision） | 週班 | 每週日 | c24 新店精睿泌尿科 | vision_scraper.py |

特殊注意（解析差異）:
  c25 上禾: HTML 用 `<h2>醫師名</h2>` 格式，其他 CXMS 用 `<br>醫師名`
  c19 得揚: 日期有時顯示上週（系統 bug），以星期幾判斷
  二診: c02 維恩、c03 富新、c05 昌惟、c07 杏光、c20 力康均有一診/二診，解析時需處理多診
  c02 維恩: CXMS 可能不即時反映特聘醫師，以公告圖為準

</clinic-types>

<schema label="schedules.json 核心欄位 | 完整 schema 見 Spec.md">
meta: generated_at | week_start | week_end | version
clinics[]: id | name | color | source_url | schedule_type | whitelist[] | blacklist[]
sessions[]: id | doctor_name | clinic_id | date | slot(morning/afternoon/evening/other) | time_label | source_note
</schema>

<rules>

WEEK-DEFINITION: 一週的第一天是星期一（Monday）| 本週 = Mon~Sun | 下週 = 下個 Mon~Sun

UPDATE-WORKFLOW:
  step-1: 掃描 schedules.json，列出「接下來一週」各診所 session 覆蓋狀況
  step-2: 產出缺漏清單（❌ 無資料 / ⚠️ 部分缺漏），確認哪些需要更新
  step-3: 依清單逐一執行爬蟲或手動補錄（詳細步驟見 SOP.md）
  step-4: 更新後重新掃描 + 衝突檢查，確認覆蓋完整
  script: |
    python3 -c "
    import json
    from datetime import datetime, timedelta
    from collections import defaultdict
    with open('schedules.json') as f: data = json.load(f)
    clinics = {c['id']: c for c in data['clinics']}
    today = datetime.now()
    monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    if today.weekday() == 6: monday = today + timedelta(days=1)
    dates = [(monday + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    print(f'檢查範圍: {dates[0]} ~ {dates[-1]}')
    clinic_sessions = defaultdict(list)
    for s in data['sessions']:
        if s['date'] in dates: clinic_sessions[s['clinic_id']].append(s)
    for c in sorted(clinics.values(), key=lambda x: x['id']):
        cid, name = c['id'], c['name']
        stype = c.get('schedule_type', '?')
        sessions = clinic_sessions.get(cid, [])
        covered = sorted(set(s['date'] for s in sessions))
        flag = '❌' if not sessions else ''
        covered_str = ', '.join(d[5:] for d in covered) if covered else '無資料'
        print(f'{cid:<5} {name:<12} {stype:<10} {len(sessions):<4} {covered_str} {flag}')
    "

CONFLICT-CHECK: → SOP.md「衝突檢查指令」區塊
OCR-CORRECTIONS: → scraper/ocr_corrections.md

PAIN-POINTS:
  core: 7 種來源類型無法全自動化，需半人工維護
  fb: FB 月班表需截圖後人工轉錄

</rules>

<commands label="快速參考">
# 覆蓋檢查（上方 UPDATE-WORKFLOW script）
# 延伸固定班表（每月月初，B2/D — 不含 C3）
python3 scraper/extend_fixed.py
# CXMS 快照（A 類型，每週）
python3 scraper/web_validator.py --all-cxms
python3 scraper/web_validator.py --clinic c02
# FB 截圖（B1 類型）
python3 scraper/fb_snapshot.py --all
python3 scraper/fb_snapshot.py --status
# 靜態圖片驗證（D 類型）
python3 scraper/image_validator.py --status
# Vision.com.tw（E 類型，每週）
python3 scraper/vision_scraper.py --clinic c24 --weeks 5
python3 scraper/vision_scraper.py --clinic c24 --weeks 5 --output /tmp/jr_sessions.json
# hixcare 線上系統（A-hix，每週；c03 富新）
python3 scraper/hixcare_scraper.py --clinic c03                    # 列印本週
python3 scraper/hixcare_scraper.py --clinic c03 --update-schedules # 寫回 schedules.json
# 新店高美（C1 官網月班表）
python3 scraper/kaomei_scraper.py --print-weekly
python3 scraper/kaomei_scraper.py --start-date 2026-06-15 --months 2 --update-schedules
# 104 新成立診所爬蟲
python3 104/104-clinic-scraper.py
</commands>

<debt>
session-id-legacy: c04/c05 2月底舊格式 ID（da_m2 等）使用 weekday 編號，格式與新格式不一致
</debt>

<tool name="104-clinic-scraper">
file: 104/104-clinic-scraper.py
purpose: 爬 104 人力銀行，搜尋台北市+新北市新成立/籌備中的診所職缺
</tool>
