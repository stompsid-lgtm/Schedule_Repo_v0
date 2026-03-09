# scraper（Schedule_Repo_v0）

## 專案定位

半自動化診所排班資料管理系統。從 22 家診所的多種來源（CXMS 網站、Facebook、官網、靜態圖片）抓取門診班表，統一寫入 `schedules.json`，供 `index.html` PWA 前端顯示。

- Remote: `stompsid-lgtm/Schedule_Repo_v0`（private）
- SOP 版本：v1.6

## 目錄結構

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

## 22 家診所分類

| 類型 | 說明 | 診所 |
|------|------|------|
| A（CXMS） | HTTP 直抓靜態 HTML，每週更新 | c02 維恩、c03 富新、c04 得安、c05 昌惟、c06 昌禾、c07 杏光、c19 得揚、c20 力康 |
| B1（FB 月班） | 截圖後人工轉錄，月底更新 | c09 健維、c17 仁祐、c22 順安 |
| B2（FB 固定） | 每月月初用 extend_fixed.py 延伸 | c01 禾安、c12 陳正傑 |
| C1（官網月） | 截圖後人工轉錄，月底更新 | c15 誠陽、c16 康澤 |
| C2（官網週） | 每週更新 | c21 永馨 |
| C3（官網固定） | 每月確認 + 延伸 | c10 板橋維力、c11 土城維力、c18 祥明 |
| D（靜態圖片） | 每 6 個月驗證 + 每月延伸 | c08 正陽、c13 悅滿意永和、c14 悅滿意新店 |

## 核心痛點

- 資料來源異質（7 種類型），無法全自動化，需半人工維護
- FB 月班表貼文需截圖後人工轉錄，無法程式化解析
- OCR 辨識醫師名字容易出錯（見 scraper/ocr_corrections.md）
- 維力骨科（c10/c11）OCR 邏輯尚未完成
- 無 .gitignore，snapshots/ 原始截圖全部進 Git（repo 會越來越大）

## 資料結構

### schedules.json

```json
{
  "meta": {
    "generated_at": "2026-03-09T00:00:00+08:00",
    "week_start": "2026-03-09",
    "week_end": "2026-03-13",
    "version": "1.0"
  },
  "clinics": [{
    "id": "c01",
    "name": "禾安復健科",
    "color": "#4d9eff",
    "source_url": "https://...",
    "schedule_type": "B2",
    "whitelist": ["陳柏誠"],
    "blacklist": []
  }],
  "sessions": [{
    "id": "c01_m_0309_c",
    "doctor_name": "陳柏誠",
    "clinic_id": "c01",
    "date": "2026-03-09",
    "slot": "morning",
    "time_label": "早診 09:00–12:00",
    "source_note": "固定班表延伸"
  }]
}
```

`slot` 值：`morning` / `afternoon` / `evening` / `other`

## 當前進度

- SOP v1.6 穩定，22 家診所分類與更新流程明確
- Claude Code 自主發現並修正 c09 健維（6 筆）和 c16 康澤（9 筆）錯誤（2026-03-05）
- extend_fixed.py 已完成並整合使用

## 已知技術債

- `weili_scraper.py`：OCR 提取邏輯待實作（目前返回示例資料）
- `manual_input_tool.py`：尚未開發（規劃中）
- 無 .gitignore：snapshots/ 快照全部進 Git，repo 體積會持續增加
- CXMS 用 HTTP 非 HTTPS 爬取（目前有效，潛在安全警告）

## 常用指令

```bash
# 延伸固定班表（每月月初執行，涵蓋 B2/C3/D 類型）
python3 scraper/extend_fixed.py

# CXMS 診所快照（A 類型，每週）
python3 scraper/web_validator.py --all-cxms
python3 scraper/web_validator.py --clinic c02   # 單一診所

# FB 截圖（B1 類型）
python3 scraper/fb_snapshot.py --all
python3 scraper/fb_snapshot.py --clinic c09
python3 scraper/fb_snapshot.py --status        # 查看截圖狀態

# 靜態圖片驗證（D 類型）
python3 scraper/image_validator.py --status
python3 scraper/image_validator.py --update c08 --note "已確認"
```

## OCR 常見錯誤（查 ocr_corrections.md）

| 診所 | OCR 錯誤 | 正確名稱 |
|------|---------|----------|
| c22 順安 | 滕學淵 | 滕學澍 |
| c10 板橋維力 | 高達駿、高道賢 | 高逢駿 |
| c10 板橋維力 | 許芳倫 | 許芳偉 |
