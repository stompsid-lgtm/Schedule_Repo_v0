# Spec.md — 門診日曆 PWA

## 這個 App 在做什麼？

「門診日曆」是一個給家庭成員（主要是媽媽）使用的私人工具，用來查看多家骨科/復健科診所的醫師排班。

資料來源是 `schedules.json`，由 `scraper/` 目錄下的工具配合人工維護。詳細更新流程請參閱 `SOP.md`。

---

## 使用者流程

### 查看排班
1. 打開 App（已加入主畫面，以 PWA 形式執行）
14. 預設顯示「2天視圖」（今天 + 明天），按左右箭頭切換日期（每次滑動 1 天）
15. 自動跳過週六、週日（只顯示平日）
3. 每個格子顯示該時段（早診/下午/晚上）有哪些醫師在哪家診所看診
4. 點擊醫師 chip → 底部資訊卡彈出，顯示：看診時段、診所名稱、日期

### 篩選特定醫師
1. 點擊任一醫師 chip → 底部資訊卡出現「🔍 篩選此醫師」按鈕
2. 點擊按鈕 → 該醫師的所有 chip 高亮（藍色外框），其他 chip 變暗
3. 篩選狀態列出現在導覽列下方，顯示「🔍 篩選醫師：XXX」
4. 點擊「✕ 取消篩選」→ 恢復正常

### 篩選特定診所
1. 點擊導覽列右側「篩選診所」下拉選單
2. 選擇診所 → 該診所所有醫師 chip 高亮，其他變暗
3. 點擊「✕ 取消篩選」→ 恢復正常

### 切換視圖
- 右上角「2天」/「週」按鈕切換視圖
32. - 週視圖顯示週一到週五

### 更新資料
- 在日曆區域向下拉（Pull to Refresh）→ 重新從 GitHub Pages 載入 `schedules.json`

### 設定頁
- 點擊右上角 ⚙️ → 進入設定頁
- 可查看「使用說明」
- 可展開各診所，手動 override 醫師顯示/隱藏（優先於 JSON 白/黑名單）

---

## 技術限制

| 限制 | 說明 |
|------|------|
| **單一 HTML 檔案** | 所有 HTML / CSS / JS 都在 `index.html`，不使用 build tool |
| **PWA** | 支援「加入主畫面」，`apple-mobile-web-app-capable`，無 service worker（不需離線） |
| **靜態 JSON** | 資料來自 `schedules.json`，部署在 GitHub Pages，App 啟動時 fetch |
| **無後端** | 沒有 API、沒有資料庫，所有狀態存在 `localStorage` |
| **無框架** | 純 Vanilla JS + CSS，不用 React/Vue/Tailwind |
|53. **行動裝置優先** | iOS Dark Mode 設計風格，緊湊佈局，SVG Icon 內嵌 |
| **繁體中文** | UI 全中文，`lang="zh-Hant"` |

---

## 資料格式（`schedules.json`）

```json
{
  "meta": { "generated_at": "2026-02-18T04:00:00Z" },
  "clinics": [
    {
      "id": "c01",
      "name": "禾安復健科",
      "color": "#4d9eff",
      "whitelist": ["陳柏誠"],
      "blacklist": []
    }
  ],
  "sessions": [
    {
      "id": "c01_20260218_morning_陳柏誠",
      "clinic_id": "c01",
      "doctor_name": "陳柏誠",
      "date": "2026-02-18",
      "slot": "morning",
      "time_label": "早診 09:00–12:00"
    }
  ]
}
```

- `whitelist`：只顯示名單內的醫師（空陣列 = 全顯示）
- `blacklist`：隱藏名單內的醫師
- `slot`：`morning` / `afternoon` / `evening` / `other`

---

## 開發要求

- **不引入外部依賴**：不用 npm、不用 CDN library，保持單一 HTML 可直接打開
- **不破壞現有功能**：修改前先理解 `shouldShow()`、`render()`、`togOverride()` 的邏輯
- **localStorage key**：`cc_overrides`，格式為 `{ "c01_陳柏誠": "hide" | "show" | undefined }`
- **新增診所**：只需在 `schedules.json` 的 `clinics` 和 `sessions` 加資料，不需改 HTML
- **部署**：`git push origin main` → GitHub Pages 自動更新（約 1 分鐘）
- **本地測試**：`python3 -m http.server 8765`，開 `http://localhost:8765`

---

## 目錄結構

```
clinic-pwa/
├── index.html          # 整個 App（HTML + CSS + JS）
├── schedules.json      # 排班資料（由 scraper 維護）
├── Spec.md             # 本文件
├── Log.md              # 開發日誌
├── SOP.md              # 門診班表資料更新 SOP（標準作業程序）
└── scraper/
    ├── ocr_corrections.md  # OCR 辨識比對修正清單
    ├── web_validator.py    # CXMS 網站爬取
    ├── fb_snapshot.py      # Facebook / LINE VOOM 截圖
    ├── image_validator.py  # 圖片來源驗證
    ├── weili_scraper.py    # 維力骨科（Selenium）
    └── snapshots/          # 各診所快照存放
```
