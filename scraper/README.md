# 診所排班資料爬蟲與驗證工具

**⚠️ 重要：詳細的操作流程與更新頻率，請以根目錄的 `SOP.md` 為準。**

本目錄下的 Script 為輔助工具，用於協助執行 `SOP.md` 中的部分步驟（如建立資料夾結構、檢查狀態等）。

## 📁 目錄結構

```
scraper/
├── ocr_corrections.md    # OCR 辨識模糊比對清單
├── web_validator.py      # CXMS 網站爬取（輔助）
├── fb_snapshot.py        # Facebook / LINE VOOM 截圖（輔助）
├── image_validator.py    # 圖片來源驗證記錄管理
├── weili_scraper.py      # 維力骨科爬蟲（Selenium）
├── requirements.txt      # Python 依賴
└── snapshots/
    ├── image/            # 圖片來源快照（正陽、悅滿意）
          ├── schedule_transcription.md  # 人工轉錄文件
          └── verified.json              # 驗證記錄
    ├── web/              # 網站來源快照（CXMS 等）
    └── social/           # 社群媒體快照（FB、LINE VOOM）
```

## 🛠️ 輔助工具使用方式

雖然主要更新流程依賴手動或半自動（依據 SOP），以下工具仍可協助管理：

### 1. 圖片診所管理 (`image_validator.py`)
用於管理 c08(正陽)、c13(悅滿意永和)、c14(悅滿意新店) 的圖片驗證狀態。

```bash
# 查看狀態
python3 scraper/image_validator.py --status

# 初始化新診所
python3 scraper/image_validator.py --init c13
```

### 2. Facebook 截圖管理 (`fb_snapshot.py`)
主要用於檢查哪些診所需要更新截圖。

```bash
# 查看狀態
python3 scraper/fb_snapshot.py --status
```

### 3. OCR 修正記錄
當遇到 OCR 辨識問題時，請查閱並更新 `ocr_corrections.md`。

## 📋 SOP 快速摘要

請參閱 `SOP.md` 獲取完整指令與步驟。

- **每週日**：更新 8 家 CXMS 診所 + 永馨 (c21)
- **每月底**：更新 Facebook (c09, c17, c22) 與 官網月班表 (c10, c15, c16)
- **每半年**：檢查 圖片診所 (c08, c13, c14)

---
