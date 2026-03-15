# scraper（Schedule_Repo_v0）| lang:zh-TW | for-AI-parsing | optimize=compliance

<meta>
repo: stompsid-lgtm/Schedule_Repo_v0（private）
purpose: 半自動化診所排班資料管理系統（24 家診所 → schedules.json → index.html PWA）
sop-version: v1.7
</meta>

<conn label="精確保留 | 禁壓縮">

DIRECTORY:
  ```
  scraper/                             # Git root
  ├── index.html                       # 診所排班 PWA 前端
  ├── schedules.json                   # 核心資料檔（所有診所排班）
  ├── schedules.json.backup            # 備份
  ├── Spec.md                          # PWA 規格
  ├── SOP.md                           # 22 家診所更新 SOP（v1.6）
  ├── Log.md                           # 開發日誌
  └── scraper/
      ├── requirements.txt             # selenium, pillow, pytesseract, requests
      ├── web_validator.py             # CXMS 網站爬取與快照
      ├── fb_snapshot.py               # Facebook/LINE VOOM 截圖
      ├── image_validator.py           # 靜態圖片診所驗證管理
      ├── weili_scraper.py             # 維力骨科 Selenium 爬蟲（保留備用）
      ├── extend_fixed.py              # 每月初延伸固定班表 sessions
      ├── ocr_corrections.md           # OCR 易誤辨醫師名字對照表
      └── snapshots/                   # 各診所快照（web/social/image，已 gitignore）
  ```

CLINIC-TYPES:
  A（CXMS）: HTTP 直抓靜態 HTML，每週更新 → c02 維恩 | c03 富新 | c04 得安 | c05 昌惟 | c06 昌禾 | c07 杏光 | c19 得揚 | c20 力康
  B1（FB 月班）: 截圖後人工轉錄，月底更新 → c09 健維 | c17 仁祐 | c22 順安 | c23 黃石
  B2（FB 固定）: 每月月初 extend_fixed.py 延伸 → c01 禾安 | c12 陳正傑
  C1（官網月）: 截圖後人工轉錄，月底更新 → c15 誠陽 | c16 康澤
  C2（官網月）: POST API 回傳未來 ~4 週資料，實質為月班表，每週更新 → c21 永馨
  C3（官網固定）: 每季/半年確認有無更新，月初 extend_fixed.py 延伸 → c10 板橋維力 | c11 土城維力 | c18 祥明
  C3-source: c10/c11 均使用 https://www.weili-clinic.com/news/category-5/post-30
  D（靜態圖片）: 每 6 個月驗證 + 每月延伸 → c08 正陽 | c13 悅滿意永和 | c14 悅滿意新店
  E（Vision.com.tw 週班）: POST /Register 直抓 HTML，每週更新 → c24 新店精睿泌尿科
  E-parser: scraper/vision_scraper.py（解析 myFunction() 呼叫，SSL 驗證已停用）
  E-query: POST date=上週一&type=1 → 回傳該週班表（系統固定返回下一週資料）

SCHEDULES-JSON-SCHEMA:
  meta: generated_at | week_start | week_end | version
  clinics[]: id | name | color | source_url | schedule_type | whitelist[] | blacklist[]
  sessions[]: id | doctor_name | clinic_id | date | slot(morning/afternoon/evening/other) | time_label | source_note

OCR-CORRECTIONS:
  c22 順安: 滕學淵 → 滕學澍
  c10 板橋維力: 高達駿/高道賢 → 高逢駿 | 許芳倫 → 許芳偉

</conn>

<rules>

UPDATE-WORKFLOW:
  step-1: 掃描 schedules.json，列出「接下來一週」各診所 session 覆蓋狀況
  step-2: 產出缺漏清單（❌ 無資料 / ⚠️ 部分缺漏），確認哪些需要更新
  step-3: 依清單逐一執行爬蟲或手動補錄
  step-4: 更新後重新掃描，確認覆蓋完整
  script: |
    python3 -c "
    import json
    from datetime import datetime, timedelta
    from collections import defaultdict
    with open('schedules.json') as f: data = json.load(f)
    clinics = {c['id']: c for c in data['clinics']}
    today = datetime.now()
    # 下週一到週日
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

PAIN-POINTS:
  core: 7 種來源類型無法全自動化，需半人工維護
  fb: FB 月班表需截圖後人工轉錄
  ocr: 醫師名字易辨錯（見 scraper/ocr_corrections.md）

</rules>

<debt>
session-id-legacy: c04/c05 2月底舊格式 ID（da_m2 等）使用 weekday 編號，已修正碰撞，但格式與新格式不一致
</debt>

<ref label="on-demand | Read when needed">

SOP.md → 22 家診所更新 SOP（v1.6）
Log.md → 開發日誌
scraper/ocr_corrections.md → OCR 易誤辨醫師名字對照表

COMMANDS:
  # 延伸固定班表（每月月初，B2/C3/D 類型）
  python3 scraper/extend_fixed.py

  # CXMS 快照（A 類型，每週）
  python3 scraper/web_validator.py --all-cxms
  python3 scraper/web_validator.py --clinic c02

  # FB 截圖（B1 類型）
  python3 scraper/fb_snapshot.py --all
  python3 scraper/fb_snapshot.py --clinic c09
  python3 scraper/fb_snapshot.py --status

  # 靜態圖片驗證（D 類型）
  python3 scraper/image_validator.py --status
  python3 scraper/image_validator.py --update c08 --note "已確認"

  # Vision.com.tw 班表（E 類型，每週）
  python3 scraper/vision_scraper.py --clinic c24 --weeks 5
  python3 scraper/vision_scraper.py --clinic c24 --weeks 5 --output /tmp/jr_sessions.json

  # 104 新成立診所爬蟲（台北市+新北市）
  python3 104-clinic-scraper.py                    # 終端印出結果
  python3 104-clinic-scraper.py --out results.json # 匯出 JSON

</ref>

<tool name="104-clinic-scraper">
file: 104-clinic-scraper.py
purpose: 爬 104 人力銀行，搜尋台北市+新北市新成立/籌備中的診所職缺
api: https://www.104.com.tw/jobs/search/api/jobs（公開 JSON API，需帶 Referer header）
strategies:
  - 「診所（籌備處）」全形/半形直搜
  - indcat=1012001002（診所產業）+ 籌備/新成立/新開幕/即將開幕
filter:
  api-level: excludeJobKeyword=牙科,眼科,兒科,皮膚科,醫美,中醫
  post-filter: 公司名含 牙/眼科/兒科/皮膚/醫美/中醫/美學/美容/婦產/產後/月子 → 排除
  relevance: 職缺需含 籌備/新成立/新開幕/即將開幕/開幕/籌設 任一關鍵字
output: 按公司分組，🏗️=籌備處 🆕=新成立
</tool>
