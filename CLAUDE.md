# scraper（Schedule_Repo_v0）| lang:zh-TW | for-AI-parsing | optimize=compliance

<meta>
repo: stompsid-lgtm/Schedule_Repo_v0（private）
purpose: 半自動化診所排班資料管理系統（22 家診所 → schedules.json → index.html PWA）
sop-version: v1.6
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
      ├── weili_scraper.py             # 維力骨科 Selenium 爬蟲（OCR 邏輯待完成）
      ├── extend_fixed.py              # 每月初延伸固定班表 sessions
      ├── ocr_corrections.md           # OCR 易誤辨醫師名字對照表
      └── snapshots/                   # 各診所快照（web/social/image）
  ```

CLINIC-TYPES:
  A（CXMS）: HTTP 直抓靜態 HTML，每週更新 → c02 維恩 | c03 富新 | c04 得安 | c05 昌惟 | c06 昌禾 | c07 杏光 | c19 得揚 | c20 力康
  B1（FB 月班）: 截圖後人工轉錄，月底更新 → c09 健維 | c17 仁祐 | c22 順安
  B2（FB 固定）: 每月月初 extend_fixed.py 延伸 → c01 禾安 | c12 陳正傑
  C1（官網月）: 截圖後人工轉錄，月底更新 → c15 誠陽 | c16 康澤
  C2（官網週）: 每週更新 → c21 永馨
  C3（官網固定）: 每月確認 + 延伸 → c10 板橋維力 | c11 土城維力 | c18 祥明
  D（靜態圖片）: 每 6 個月驗證 + 每月延伸 → c08 正陽 | c13 悅滿意永和 | c14 悅滿意新店

SCHEDULES-JSON-SCHEMA:
  meta: generated_at | week_start | week_end | version
  clinics[]: id | name | color | source_url | schedule_type | whitelist[] | blacklist[]
  sessions[]: id | doctor_name | clinic_id | date | slot(morning/afternoon/evening/other) | time_label | source_note

OCR-CORRECTIONS:
  c22 順安: 滕學淵 → 滕學澍
  c10 板橋維力: 高達駿/高道賢 → 高逢駿 | 許芳倫 → 許芳偉

</conn>

<rules>

PAIN-POINTS:
  core: 7 種來源類型無法全自動化，需半人工維護
  fb: FB 月班表需截圖後人工轉錄
  ocr: 醫師名字易辨錯（見 scraper/ocr_corrections.md）

</rules>

<debt>
weili_scraper.py: OCR 提取邏輯待實作（目前返回示例資料）
manual_input_tool.py: 尚未開發
no-gitignore: snapshots/ 全部進 Git，repo 體積持續增加
cxms-http: 用 HTTP 非 HTTPS 爬取（目前有效，潛在安全警告）
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

</ref>
