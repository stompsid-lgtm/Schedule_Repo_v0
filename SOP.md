# 門診班表資料更新 SOP

**版本**：v1.0（2026-02-18）  
**最高守則**：資料正確性優先於一切。有疑問時，以原始來源為準，不猜測。

---

## 概覽：22 家診所分類

| 類型 | 診所 | 更新頻率 |
|------|------|---------|
| **A. CXMS 網頁** | c02 維恩、c03 富新、c04 得安、c05 昌惟、c06 昌禾、c07 土城杏光、c19 得揚、c20 力康 | 每週 |
| **B. Facebook** | c01 禾安、c09 健維、c12 陳正傑、c17 仁祐、c22 順安 | 每月（月初） |
| **C. 官方網站** | c10 板橋維力、c11 土城維力、c15 誠陽、c16 康澤、c18 祥明、c21 永馨 | 每月（月初） |
| **D. 靜態圖片** | c08 正陽、c13 悅滿意永和、c14 悅滿意新店 | 每 6 個月（或診所通知更換） |

---

## 類型 A：CXMS 網頁（8 家）

### 重要說明
- CXMS 班表透過 **AJAX 動態載入**，靜態爬蟲抓不到。必須用瀏覽器等待 JS 執行完畢。
- 班表只顯示「當週」，每週一更新。**每週一**必須重新抓取。
- 網址格式：`http://web.cxms.com.tw/{代碼}/hosp.php`

### 各診所網址

| 診所 | 代碼 | 網址 |
|------|------|------|
| c02 維恩骨科 | wn | http://web.cxms.com.tw/wn/hosp.php |
| c03 富新骨科 | fc | http://web.cxms.com.tw/fc/hosp.php |
| c04 得安診所 | da | http://web.cxms.com.tw/da/hosp.php |
| c05 昌惟骨科 | cw | http://web.cxms.com.tw/cw/hosp.php |
| c06 昌禾骨科 | ch | http://web.cxms.com.tw/ch/hosp.php |
| c07 土城杏光 | xq | http://web.cxms.com.tw/xq/hosp.php |
| c19 得揚診所 | dy | http://web.cxms.com.tw/dy/hosp.php |
| c20 力康骨科 | lk | http://web.cxms.com.tw/lk/hosp.php |

### 操作步驟（每週一執行）

1. **開啟瀏覽器**，依序訪問上表每個網址
2. **等待 3 秒**讓 AJAX 班表載入完成
3. **截圖**（全頁），儲存至：
   ```
   scraper/snapshots/web/{診所ID}/YYYYMMDD_schedule.png
   ```
   例：`scraper/snapshots/web/c03/20260223_schedule.png`
4. **讀取班表**：逐格確認醫師姓名、日期、時段（早/午/晚）
5. **對比 schedules.json**：找出差異（新增、刪除、醫師名變更）
6. **更新 schedules.json**：
   - 刪除舊的該診所所有 sessions
   - 新增本週正確 sessions
   - `id` 命名規則：`{診所縮寫}_{時段縮寫}{日期序號}`，例：`fc_m1`（富新早診第1天）
7. **驗證**：執行衝突檢查（同一醫師同一時段出現在兩家）

### 注意事項
- 若網頁顯示「本週無門診」或空白，**不要刪除**上週資料，先確認是否為假日/特殊情況
- 得揚（c19）的日期有時顯示上週日期（系統 bug），以實際星期幾判斷
- 力康（c20）有多診（一診/二診），每個時段可能有 2 位醫師，都要記錄

---

## 類型 B：Facebook（5 家）

### 重要說明
- Facebook 有反爬蟲機制，**必須手動截圖**。
- 各診所每月初發布當月門診表（圖片貼文）。
- **截圖方法**：必須點擊圖片放大後再截圖，直接截貼文預覽會被切掉。

### 各診所資訊

| 診所 | Facebook 頁面 | 醫師 | OCR 備註 |
|------|--------------|------|---------|
| c01 禾安復健科 | https://www.facebook.com/share/19qBxvUV52/ | 待確認 | — |
| c09 健維骨科 | https://www.facebook.com/JianWeiGuKeZhenSuo | 韓文江、林承翰 | — |
| c12 陳正傑骨科 | https://www.facebook.com/share/1EwsVWdZka/ | 待確認 | — |
| c17 仁祐骨科 | https://www.facebook.com/share/19wyYeXoNV/ | 待確認 | — |
| c22 順安復健科 | https://www.facebook.com/share/1AnuyYyEsi/ | 滕學淵、陳俊宇 | 「滕學淵」FB 圖片可能辨識為「滕學澍」，前兩字相同可接受 |

### 操作步驟（每月初執行）

1. **開啟 Facebook 頁面**（可能需要先登入）
2. **找到當月門診表貼文**（通常標題含「X月門診表」）
3. **點擊貼文中的圖片**，等待全尺寸圖片載入
4. **截圖**（全尺寸圖片，確保班表完整不被切掉），儲存至：
   ```
   scraper/snapshots/social/{診所ID}_{診所名}/YYYYMMDD_schedule_full.png
   ```
   例：`scraper/snapshots/social/c09_健維骨科/20260301_schedule_full.png`
5. **逐格讀取**：確認每天每個時段的醫師姓名
6. **特別注意**：
   - 圖片中的「代診」標示（代診醫師只在特定日期，不是固定班）
   - 「停診」標示（該時段無門診）
   - 228、國慶等假日的特殊安排
7. **更新 schedules.json**：只記錄「本週」的 sessions（不記錄整月）

### 注意事項
- 若 Facebook 要求登入才能看貼文，需要先登入帳號
- 若貼文圖片有更新（月中修正），以最新版本為準
- 健維骨科（c09）：週四下午林承翰醫師門診時間到 17:15（17:00 截止掛號）

---

## 類型 C：官方網站（6 家）

### 各診所資訊

| 診所 | 網址 | 班表類型 | 醫師 |
|------|------|---------|------|
| c10 板橋維力 | https://www.weili-clinic.com/news/category-5/post-30 | 固定週班（年度） | 高逢駿、陳書佑、林茂森、陳奕成、許芳偉 |
| c11 土城維力 | https://www.weili-clinic.com/news/category-5/post-30 | 固定週班（年度） | 劉大維、張晉魁、楊欣達 |
| c15 誠陽復健科 | https://sites.google.com/view/chengyang-clinic | 待確認 | 待確認 |
| c16 康澤復健科 | https://kangzereh.com | 待確認 | 待確認 |
| c18 祥明診所 | https://www.shiangming.com/time.php | 待確認 | 待確認 |
| c21 永馨復健科 | https://www.sc-dr.com.tw | 待確認 | 待確認 |

> ⚠️ **OCR 備註**：板橋維力「高逢駿」，網站文字 OCR 可能辨識為「高達駿」，使用者確認正確名稱為「高逢駿」。

### 操作步驟（每月初執行）

1. **開啟診所網址**，找到門診時間/班表頁面
2. **截圖**，儲存至：
   ```
   scraper/snapshots/web/{診所ID}/YYYYMMDD_schedule.png
   ```
3. **讀取班表**：確認醫師姓名、星期、時段
4. **對比 schedules.json**：若固定週班無變動，只需確認本週日期對應正確
5. **更新 schedules.json**：若有變動才修改

#### 板橋維力（c10）與土城維力（c11）特殊說明
- 兩院區**共用同一個網頁**：https://www.weili-clinic.com/news/category-5/post-30
- 頁面上方為**板橋**院區班表，下方為**土城**院區班表
- 班表為年度固定班，通常每年初更新一次
- 土城維力（c11）週六下午為「輪診」，需確認當週實際醫師

---

## 類型 D：靜態圖片（3 家）

### 各診所資訊

| 診所 | 圖片來源 | 醫師 | 轉錄文件 |
|------|---------|------|---------|
| c08 正陽骨科 | 使用者提供（FB 截圖） | 蘇哲惟、黃旭東、黃英庭、曾鵬文、蔡馥如 | `scraper/snapshots/image/c08_正陽骨科/schedule_transcription.md` |
| c13 悅滿意永和 | 使用者提供（固定班表圖片） | 悅滿意江、悅滿意李、悅滿意王、悅滿意丁、悅滿意林 | `scraper/snapshots/image/c13_悅滿意永和/schedule_transcription.md` |
| c14 悅滿意新店 | 使用者提供（固定班表圖片） | 悅滿意李、悅滿意丁、悅滿意王、悅滿意江、悅滿意羅 | `scraper/snapshots/image/c14_悅滿意新店/schedule_transcription.md` |

> ℹ️ **醫師命名規則**：悅滿意兩院區的醫師圖片只顯示姓氏（「江醫師」），系統中統一用「悅滿意江」格式，避免與其他診所同姓醫師混淆。

### 操作步驟（每 6 個月，或診所通知班表更換時）

1. **取得新圖片**：
   - 正陽骨科：請診所提供最新班表圖片，或從 Facebook 貼文截圖
   - 悅滿意兩院區：請診所提供最新固定班表圖片
2. **儲存圖片**至：
   ```
   scraper/snapshots/image/{診所ID}_{診所名}/YYYYMMDD_source.png
   ```
3. **人工轉錄**：逐格讀取圖片，填入 `schedule_transcription.md`：
   - 複製現有的 `schedule_transcription.md` 為模板
   - 更新日期、班表內容
4. **對比舊資料**：找出與 schedules.json 的差異
5. **更新 schedules.json**：
   - 刪除該診所所有舊 sessions
   - 新增正確 sessions
6. **更新 verified.json**：
   ```json
   {
     "verified": true,
     "verified_at": "YYYY-MM-DDTHH:MM:SS+08:00",
     "verified_by": "user_provided_image",
     "image_files": ["YYYYMMDD_source.png"]
   }
   ```

---

## 每週更新流程（完整）

```
每週一（或週日晚上）執行：

1. 類型 A（CXMS）：8 家全部重新抓取
   → 依序開啟 8 個網址 → 等待 3 秒 → 截圖 → 讀取 → 更新

2. 衝突檢查：
   python3 -c "
   import json
   with open('schedules.json') as f: data = json.load(f)
   from collections import defaultdict
   conflicts = defaultdict(list)
   for s in data['sessions']:
       key = (s['doctor_name'], s['date'], s['slot'])
       conflicts[key].append(s['clinic_id'])
   for key, clinics in conflicts.items():
       if len(clinics) > 1:
           print(f'衝突: {key} → {clinics}')
   "

3. 類型 B/C（FB/官網）：每月初才需要更新，平時跳過

4. Git commit：
   git add schedules.json scraper/snapshots/
   git commit -m "週班表更新 YYYY-MM-DD"
   git push
```

---

## 常見問題

### Q: 醫師名字 OCR 辨識不確定怎麼辦？
- 在 `schedules.json` 的 `source_note` 欄位記錄：`OCR備註：圖片辨識為「XXX」，確認名稱為「YYY」`
- 前兩字相同的辨識結果通常可接受（例：滕學澍 vs 滕學淵）
- 有疑問時，以診所官方資料（掛號系統、名片）為準

### Q: 同一醫師出現在兩家診所怎麼辦？
- 先確認是否真的是同一人（同名不同人的情況存在）
- 若確認是同一人，確認哪家診所的資料正確（通常以 CXMS 或官網為準）
- 刪除錯誤的那筆，在 `source_note` 記錄原因

### Q: 診所某天沒有門診怎麼辦？
- 假日（228、國慶等）：只記錄有開診的時段，空白時段不建立 session
- 停診通知：刪除該時段的 session，可在 `source_note` 記錄「停診」

### Q: 班表圖片看不清楚怎麼辦？
- Facebook：點擊圖片放大後再截圖（不要直接截貼文預覽）
- 仍不清楚：致電診所確認，或等下週更新的圖片

---

## 快照目錄結構

```
scraper/snapshots/
├── image/                    # 靜態圖片診所
│   ├── c08_正陽骨科/
│   │   ├── schedule_transcription.md   # 人工轉錄
│   │   └── verified.json
│   ├── c13_悅滿意永和/
│   │   ├── schedule_transcription.md
│   │   └── verified.json
│   └── c14_悅滿意新店/
│       ├── schedule_transcription.md
│       └── verified.json
├── social/                   # Facebook 截圖
│   ├── c01_禾安復健科/
│   ├── c09_健維骨科/
│   ├── c12_陳正傑骨科/
│   ├── c17_仁祐骨科/
│   └── c22_順安復健科/
└── web/                      # CXMS + 官方網站截圖
    ├── c02/ ~ c07/           # CXMS（每週更新）
    ├── c10/ c11/             # 維力官網
    ├── c19/ c20/             # CXMS
    └── c02/                  # 維恩（HTML 快照）
```

---

*最後更新：2026-02-18*
