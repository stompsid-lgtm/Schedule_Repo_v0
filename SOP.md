# 門診班表資料更新 SOP

**版本**：v1.2（2026-02-18）  
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

### 重要說明（2026-02-21 更新）

> ✅ **不需要開瀏覽器、不需要截圖、不需要 OCR。**
>
> 班表資料直接嵌在靜態 HTML 裡（JS 只是每 2 分鐘刷新用，非首次載入必要）。
> 用 `curl` 以 **HTTP**（非 HTTPS）抓取即可取得完整資料。

**舊認知（已更正）**：~~班表透過 AJAX 動態載入，靜態爬蟲抓不到，必須用瀏覽器~~

- 班表只顯示「當週」，**每週日**預先抓取下週資料

### 各診所代碼與網址

| 診所 | 代碼 | 網址 |
|------|------|------|
| c02 維恩骨科 | `wn` | http://web.cxms.com.tw/wn/hosp.php |
| c03 富新骨科 | `fc` | http://web.cxms.com.tw/fc/hosp.php |
| c04 得安診所 | `da` | http://web.cxms.com.tw/da/hosp.php |
| c05 昌惟骨科 | `cw` | http://web.cxms.com.tw/cw/hosp.php |
| c06 昌禾骨科 | `ch` | http://web.cxms.com.tw/ch/hosp.php |
| c07 土城杏光 | `xq` | http://web.cxms.com.tw/xq/hosp.php |
| c19 得揚診所 | `dy` | http://web.cxms.com.tw/dy/hosp.php |
| c20 力康骨科 | `lk` | http://web.cxms.com.tw/lk/hosp.php |

### 操作步驟（每週日執行，抓取下週班表）

#### Step 1：一次下載所有 HTML

```bash
for code in wn fc da cw ch xq dy lk; do
  curl -s -L --max-time 10 "http://web.cxms.com.tw/$code/hosp.php" \
    > /tmp/cxms_$code.html
  echo "$code: $(wc -c < /tmp/cxms_$code.html) bytes"
done
```

> ⚠️ 必須用 **HTTP**（非 HTTPS），HTTPS 會拒絕連線。

#### Step 2：解析班表

```python
import re, json

clinic_map = {
    'wn': ('c02','維恩骨科'),  'fc': ('c03','富新骨科'),
    'da': ('c04','得安診所'),  'cw': ('c05','昌惟骨科'),
    'ch': ('c06','昌禾骨科'),  'xq': ('c07','土城杏光'),
    'dy': ('c19','得揚診所'),  'lk': ('c20','力康骨科'),
}
days = ['Mon','Tue','Wed','Thu','Fri','Sat']

for code, (cid, name) in clinic_map.items():
    with open(f'/tmp/cxms_{code}.html', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    row_pattern = re.compile(r"<tr align='center'[^>]*>(.*?)</tr>", re.DOTALL)
    cell_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)
    doc_pattern  = re.compile(r'<br>\s*([\u4e00-\u9fff]+)', re.DOTALL)

    print(f'\n=== {cid} {name} ===')
    for row in row_pattern.finditer(html):
        cells = cell_pattern.findall(row.group(1))
        if not cells: continue
        diag = re.sub(r'<[^>]+>', '', cells[0]).strip()
        if not diag: continue
        day_docs = []
        for cell in cells[1:]:
            m = doc_pattern.search(cell)
            day_docs.append(m.group(1) if m else '空')
        parts = [f'{d}={doc}' for d, doc in zip(days, day_docs)]
        print(f'  {diag}: {" | ".join(parts)}')
```

#### Step 3：對比並更新 schedules.json

1. 比對輸出與 schedules.json 現有 sessions
2. 刪除該診所本週舊 sessions
3. 新增正確 sessions（注意黑名單醫師仍要收錄，UI 會過濾）
4. 執行衝突檢查（見下方）
5. `git commit & push`

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

| 診所 | 預約頁面 |
|------|----------|
| c21 永馨復健科 | https://www.sc-dr.com.tw/progress/3531035027.php |

### 操作步驟（每週日）

1. **抓取 API**（`hospid=3531035027`，民國年格式，範圍 4 週）：

```bash
# 計算今日民國年日期（例：2026-02-21 → 115.02.21）
YEAR=$(($(date +%Y) - 1911))
FIRSTDAY="${YEAR}.$(date +%m.%d)"
# lastday = +28天，手動計算或用 Python
curl -s -X POST \
  -d "hospid=3531035027&firstday=${FIRSTDAY}&lastday=${YEAR}.$(date -v+28d +%m.%d)" \
  "https://www.sc-dr.com.tw/progress/ajax/getreserve.php" \
  > /tmp/yongxin_api.json
```

2. **解析欄位**：
   - `infirm1x` = 上午（09:00–12:00），`infirm2x` = 下午（14:30–17:30），`infirm3x` = 晚上（18:00–21:00）
   - 醫師欄格式：`姓名      號碼`，取名字部分（strip 後取首段）
   - 日期格式：民國年 `115.02.23` → Gregorian `2026-02-23`（+1911）

3. **更新 sessions**：刪除 `clinic_id == 'c21'` 的所有舊 sessions，寫入 API 傳回的有資料日期（跳過空白日）

4. **ID 命名**：`yx_{m|a|e}_{MMDD}`（例：`yx_m_0223`）

5. **快照**：API JSON 存至 `scraper/snapshots/web/c21/YYYYMMDD_getreserve.json`

---

## 類型 C3：官方網站固定班表（2 家）— 每月檢查

| 診所 | 網址 | 說明 |
|------|------|------|
| c11 土城維力 | https://www.weili-clinic.com/news/category-5/post-30 | 固定週班，每月確認有無更新 |
| c18 祥明診所 | https://www.shiangming.com/time.php | 固定週班，每月確認有無更新 |

### 操作步驟（每月底）

1. **curl 抓取靜態 HTML**：

```bash
# c11 土城維力
curl -s -L "https://www.weili-clinic.com/news/category-5/post-30" \
  > scraper/snapshots/web/c11/YYYYMMDD_html.html

# c18 祥明診所
curl -s -L "https://www.shiangming.com/time.php" \
  > scraper/snapshots/web/c18/YYYYMMDD_html.html
```

2. **對比上月快照**：若班表無變動，沿用舊 sessions 資料（更新日期即可）
3. 若有變動：重建該診所所有 sessions（刪舊、依新班表補入），記錄變動原因

**sessions 需涵蓋當月 + 下月（約 8 週）**；固定班表每週相同，用 Python 依週期批次生成日期。

#### 土城維力（c11）特殊說明
- 與板橋維力共用同一網頁，**土城在下方**
- 週六資料不顯示於 App，不需記錄週六 sessions

#### 祥明診所（c18）班表摘要（截至 2026-02）
| 診 | 一 | 二 | 三 | 四 | 五 |
|----|----|----|----|----|-----|
| 早 | 黃有明、夏漢詳 | 黃有明、夏漢詳 | 黃有明、楊正楓 | 黃有明 | 黃有明、楊正楓 |
| 午 | 黃有明 | 楊正楓 | 黃有明、夏漢詳 | 楊正楓 | 楊正楓 |
| 晚 | 黃有明 | 楊正楓 | 夏漢詳 | 楊正楓 | 夏漢詳 |

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
【每週日執行，抓取下週班表】
□ 類型 A（CXMS 8 家）：curl 抓 HTML → Python 解析 → 更新 schedules.json（下週）
□ 類型 C2（永馨 c21）：截圖 → 讀取 → 更新 schedules.json（下週）
□ 衝突檢查（見下方）
□ git commit & push

【每月底執行（抓取下個月）】
□ 類型 B1（FB 月班表：c09/c17/c22）：截大圖 → 讀取整月 → 新增下月 sessions（不刪本月）
□ 類型 C1（官網月班表：c10/c15/c16）：截圖 → 讀取整月 → 新增下月 sessions（不刪本月）
□ 類型 C3（固定班表檢查：c11/c18）：截圖 → 對比上月 → 有變動才更新
□ git commit & push
```

> ⚠️ **月班表更新原則**：月底更新下個月資料時，**不刪除當月尚未結束的 sessions**。
> 例：2 月底更新 3 月班表時，2 月份 sessions 保留不動，直到 3 月 1 日後才可清除。

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
1. **先問使用者**確認正確名稱，不要自行猜測
2. 得到確認後，記錄到兩個地方：
   - `schedules.json` 的 `source_note`：`OCR備註：圖片辨識為「XXX」，確認名稱為「YYY」`
   - `scraper/ocr_corrections.md`：更新模糊比對清單（見下方）
3. 前兩字相同的辨識結果通常可接受（例：滕學澍 vs 滕學淵）

### Q: 診所某天沒有門診怎麼辦？
假日或停診：不建立 session，空白即代表無門診。

### Q: 月班表要寫入幾週的資料？
整個月。例如 3 月班表，寫入 3/1 到 3/31 所有有門診的 sessions。

### Q: 更新下個月班表時，要刪除當月資料嗎？
**不刪**。月底更新下個月資料時，當月 sessions 保留，等當月結束後才清除。
例：2/28 更新 3 月班表 → 2 月 sessions 繼續保留到 2/28 結束。

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

*最後更新：2026-02-21 v1.3*
