# 門診班表資料更新 SOP

**版本**：v1.1（2026-02-18）  
**最高守則**：資料正確性優先於一切。有疑問時，以原始來源為準，不猜測。

---

## 概覽：22 家診所分類

| 類型 | 班表性質 | 更新頻率 | 診所 |
|------|---------|---------|------|
| **A. CXMS 網頁** | 週班表 | **每週** | c02 維恩、c03 富新、c04 得安、c05 昌惟、c06 昌禾、c07 土城杏光、c19 得揚、c20 力康 |
| **B1. Facebook（月班表）** | 月班表 | **前月月底** | c09 健維、c17 仁祐、c22 順安 |
| **B2. Facebook（固定班表）** | 固定班表 | **不需更新** | c01 禾安、c12 陳正傑 |
| **C1. 官方網站（月班表）** | 月班表 | **前月月底** | c10 板橋維力、c15 誠陽、c16 康澤 |
| **C2. 官方網站（週班表）** | 週班表 | **每週** | c21 永馨 |
| **C3. 官方網站（固定班表）** | 固定班表 | **每月檢查** | c11 土城維力、c18 祥明 |
| **D. 靜態圖片** | 固定班表 | **每 6 個月** | c08 正陽、c13 悅滿意永和、c14 悅滿意新店 |

### 衝突判斷規則
- 目前名單內**無醫師重複姓名**，同名必定同人
- 跨院看診是可能的（同一醫師在不同診所），**不算衝突**
- **真正的衝突**：同一醫師在**同一天的同一時段（早/午/晚）**出現在兩家診所 → 必須修正

---

## 類型 A：CXMS 網頁（8 家）— 每週更新

### 重要說明
- 班表透過 **AJAX 動態載入**，靜態爬蟲抓不到，必須用瀏覽器等待 JS 執行
- 班表只顯示「當週」，**每週一**必須重新抓取
- c02 維恩骨科：舊快照為 HTML 格式（靜態爬蟲遺留），已於 2026-02-18 補截圖

### 各診所網址

| 診所 | 網址 |
|------|------|
| c02 維恩骨科 | http://web.cxms.com.tw/wn/hosp.php |
| c03 富新骨科 | http://web.cxms.com.tw/fc/hosp.php |
| c04 得安診所 | http://web.cxms.com.tw/da/hosp.php |
| c05 昌惟骨科 | http://web.cxms.com.tw/cw/hosp.php |
| c06 昌禾骨科 | http://web.cxms.com.tw/ch/hosp.php |
| c07 土城杏光 | http://web.cxms.com.tw/xq/hosp.php |
| c19 得揚診所 | http://web.cxms.com.tw/dy/hosp.php |
| c20 力康骨科 | http://web.cxms.com.tw/lk/hosp.php |

### 操作步驟（每週一執行）

1. 依序開啟上表 8 個網址，**等待 3 秒**讓 AJAX 載入
2. **截圖**（全頁），儲存至：
   ```
   scraper/snapshots/web/{診所ID}/YYYYMMDD_schedule.png
   ```
3. 逐格讀取：醫師姓名 × 日期 × 時段（早/午/晚）
4. 對比 schedules.json，找出差異
5. 更新 schedules.json：刪除該診所舊 sessions，新增本週正確 sessions
6. 執行衝突檢查（見下方）

### 特殊注意
- **得揚（c19）**：日期有時顯示上週日期（系統 bug），以實際星期幾判斷
- **力康（c20）**：每個時段可能有 2 位醫師（一診/二診），都要記錄
- 若網頁空白，先確認是否為假日，不要貿然刪除資料

---

## 類型 B1：Facebook 月班表（3 家）— 前月月底更新

### 各診所資訊

| 診所 | Facebook 頁面 | 醫師 | OCR 備註 |
|------|--------------|------|---------|
| c09 健維骨科 | https://www.facebook.com/JianWeiGuKeZhenSuo | 韓文江、林承翰 | 週四下午林承翰 17:15 結束（17:00 截止掛號） |
| c17 仁祐骨科 | https://www.facebook.com/share/19wyYeXoNV/ | 待確認 | — |
| c22 順安復健科 | https://www.facebook.com/share/1AnuyYyEsi/ | 滕學淵、陳俊宇 | 「滕學淵」FB 圖片可能辨識為「滕學澍」，前兩字相同可接受 |

### 操作步驟（每月底，抓取下個月班表）

1. 開啟 Facebook 頁面（可能需要登入）
2. 找到**下個月**門診表貼文（通常月底前幾天發布）
3. **點擊貼文中的圖片**，等待全尺寸圖片載入（不能截貼文預覽，會被切掉）
4. 截圖，儲存至：
   ```
   scraper/snapshots/social/{診所ID}_{診所名}/YYYYMMDD_schedule_full.png
   ```
5. 逐格讀取整月班表（注意代診、停診、假日標示）
6. **寫入整月 sessions**：刪除該診所下個月所有舊 sessions，新增整月正確 sessions
7. 執行衝突檢查

---

## 類型 B2：Facebook 固定班表（2 家）— 不需更新

| 診所 | Facebook 頁面 | 說明 |
|------|--------------|------|
| c01 禾安復健科 | https://www.facebook.com/share/19qBxvUV52/ | 多年不變，當作固定班表 |
| c12 陳正傑骨科 | https://www.facebook.com/share/1EwsVWdZka/ | 多年不變，當作固定班表 |

**操作**：若診所通知班表異動，才需重新截圖並更新。平時不需定期更新。

---

## 類型 C1：官方網站月班表（3 家）— 前月月底更新

| 診所 | 網址 | 醫師 | OCR 備註 |
|------|------|------|---------|
| c10 板橋維力 | https://www.weili-clinic.com/news/category-5/post-30 | 高逢駿、陳書佑、林茂森、陳奕成、許芳偉 | 「高逢駿」網站文字 OCR 可能辨識為「高達駿」，可接受 |
| c15 誠陽復健科 | https://sites.google.com/view/chengyang-clinic | 待確認 | — |
| c16 康澤復健科 | https://kangzereh.com | 待確認 | — |

### 操作步驟（每月底，抓取下個月班表）

1. 開啟診所網址，找到月班表頁面
2. 截圖，儲存至：
   ```
   scraper/snapshots/web/{診所ID}/YYYYMMDD_schedule.png
   ```
3. 逐格讀取整月班表
4. **寫入整月 sessions**：刪除該診所下個月所有舊 sessions，新增整月正確 sessions

#### 板橋維力（c10）特殊說明
- 與土城維力共用同一網頁，**板橋在上方**，土城在下方
- 月班表：每月底更新下個月班表

---

## 類型 C2：官方網站週班表（1 家）— 每週更新

| 診所 | 網址 |
|------|------|
| c21 永馨復健科 | https://www.sc-dr.com.tw |

**操作**：同類型 A（CXMS），每週一開啟網頁截圖，更新當週 sessions。

---

## 類型 C3：官方網站固定班表（2 家）— 每月檢查

| 診所 | 網址 | 說明 |
|------|------|------|
| c11 土城維力 | https://www.weili-clinic.com/news/category-5/post-30 | 固定週班，每月確認有無更新 |
| c18 祥明診所 | https://www.shiangming.com/time.php | 固定週班，每月確認有無更新 |

### 操作步驟（每月底）

1. 開啟網頁，截圖
2. **對比上月截圖**：若班表無變動，沿用舊資料，不需更新 schedules.json
3. 若有變動，更新 schedules.json 並記錄變動原因

#### 土城維力（c11）特殊說明
- 與板橋維力共用同一網頁，**土城在下方**
- 週六下午為「輪診」，需確認當月實際醫師

---

## 類型 D：靜態圖片（3 家）— 每 6 個月

| 診所 | 轉錄文件 | 醫師 |
|------|---------|------|
| c08 正陽骨科 | `scraper/snapshots/image/c08_正陽骨科/schedule_transcription.md` | 蘇哲惟、黃旭東、黃英庭、曾鵬文、蔡馥如 |
| c13 悅滿意永和 | `scraper/snapshots/image/c13_悅滿意永和/schedule_transcription.md` | 悅滿意江、悅滿意李、悅滿意王、悅滿意丁、悅滿意林 |
| c14 悅滿意新店 | `scraper/snapshots/image/c14_悅滿意新店/schedule_transcription.md` | 悅滿意李、悅滿意丁、悅滿意王、悅滿意江、悅滿意羅 |

> ℹ️ 悅滿意醫師命名：圖片只顯示姓氏（「江醫師」），系統統一用「悅滿意江」格式，避免與其他診所同姓醫師混淆。

### 操作步驟（每 6 個月，或診所通知更換時）

1. 取得新圖片（請診所提供，或從 FB 截圖）
2. 儲存至：`scraper/snapshots/image/{診所ID}_{診所名}/YYYYMMDD_source.png`
3. 人工轉錄，更新 `schedule_transcription.md`
4. 對比 schedules.json，找出差異
5. 更新 schedules.json（固定班表，寫入未來數週的 sessions）
6. 更新 `verified.json`：`verified: true`、記錄日期與圖片檔名

---

## 每週執行清單

```
【每週一執行】
□ 類型 A（CXMS 8 家）：截圖 → 讀取 → 更新 schedules.json
□ 類型 C2（永馨 c21）：截圖 → 讀取 → 更新 schedules.json
□ 衝突檢查（見下方）
□ git commit & push

【每月底執行（抓取下個月）】
□ 類型 B1（FB 月班表：c09/c17/c22）：截大圖 → 讀取整月 → 更新 schedules.json
□ 類型 C1（官網月班表：c10/c15/c16）：截圖 → 讀取整月 → 更新 schedules.json
□ 類型 C3（固定班表檢查：c11/c18）：截圖 → 對比上月 → 有變動才更新
□ git commit & push
```

---

## 衝突檢查指令

```python
python3 -c "
import json
from collections import defaultdict
with open('schedules.json') as f:
    data = json.load(f)
clinics = {c['id']: c['name'] for c in data['clinics']}
conflicts = defaultdict(list)
for s in data['sessions']:
    key = (s['doctor_name'], s['date'], s['slot'])
    conflicts[key].append((s['clinic_id'], clinics[s['clinic_id']]))
for key, entries in conflicts.items():
    if len(entries) > 1:
        print(f'衝突: 醫師={key[0]} 日期={key[1]} 時段={key[2]}')
        for cid, name in entries:
            print(f'  → {cid} {name}')
"
```

---

## 常見問題

### Q: OCR 辨識不確定怎麼辦？
在 `source_note` 記錄：`OCR備註：圖片辨識為「XXX」，確認名稱為「YYY」`  
前兩字相同的辨識結果通常可接受。

### Q: 診所某天沒有門診怎麼辦？
假日或停診：不建立 session，空白即代表無門診。

### Q: 月班表要寫入幾週的資料？
整個月。例如 3 月班表，寫入 3/1 到 3/31 所有有門診的 sessions。

---

## 快照目錄結構

```
scraper/snapshots/
├── image/          # 靜態圖片診所（c08/c13/c14）
│   └── {診所}/
│       ├── schedule_transcription.md
│       └── verified.json
├── social/         # Facebook 截圖（c01/c09/c12/c17/c22）
│   └── {診所}/
│       └── YYYYMMDD_schedule_full.png   ← 必須是放大後的全尺寸圖
└── web/            # CXMS + 官方網站截圖
    └── {診所ID}/
        └── YYYYMMDD_schedule.png
```

*最後更新：2026-02-18 v1.1*
