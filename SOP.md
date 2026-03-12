# 門診班表資料更新 SOP

**版本**：v1.7（2026-03-12）
**最高守則**：資料正確性優先於一切。有疑問時，以原始來源為準，不猜測。

---

## 概覽：24 家診所分類

| 類型 | 班表性質 | 更新頻率 | 診所 |
|------|---------|---------|------|
| **A. CXMS 網頁** | 週班表 | **每週** | c02 維恩、c03 富新、c04 得安、c05 昌惟、c06 昌禾、c07 土城杏光、c19 得揚、c20 力康 |
| **B1. Facebook（月班表）** | 月班表 | **前月月底** | c09 健維、c17 仁祐、c22 順安、c23 黃石 |
| **B2. Facebook（固定班表）** | 固定班表 | **每月延伸** | c01 禾安、c12 陳正傑 |
| **C1. 官方網站（月班表）** | 月班表 | **前月月底** | c15 誠陽、c16 康澤 |
| **C2. 官方網站（週班表）** | 週班表 | **每週** | c21 永馨 |
| **C3. 官方網站（固定班表）** | 固定班表 | **每月檢查** | c10 板橋維力、c11 土城維力、c18 祥明 |
| **D. 靜態圖片** | 固定班表 | **內容 6 個月、sessions 每月** | c08 正陽、c13 悅滿意永和、c14 悅滿意新店 |
| **E. Vision.com.tw 週班表** | 週班表 | **每週** | c24 新店精睿泌尿科 |

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
- **維恩（c02）**：CXMS HTML 可能不即時反映當月新增的特聘醫師，若診所有公告圖片，以公告圖片為準
- 若網頁空白，先確認是否為假日，不要貿然刪除資料

---

## 類型 B1：Facebook 月班表（3 家）— 前月月底更新

### 各診所資訊

| 診所 | Facebook 頁面 | 醫師 | OCR 備註 |
|------|--------------|------|---------|
| c09 健維骨科 | https://www.facebook.com/JianWeiGuKeZhenSuo | 韓文江、林承翰 | 週四下午林承翰看診至 17:15（17:00 截止掛號） |
| c17 仁祐骨科 | https://www.facebook.com/share/19wyYeXoNV/ | 劉彥麟、陳漢祐 | 週六早診交替（奇週=劉彥麟、偶週=陳漢祐），請每月確認 |
| c22 順安復健科 | https://www.facebook.com/share/1AnuyYyEsi/ | 滕學澍、陳俊宇 | 「滕學澍」是正確名稱，OCR 可能辨識為「滕學淵」，前兩字相同，遲竅接受 |
| c23 黃石健康診所 | https://www.facebook.com/people/%E9%BB%83%E7%9F%B3%E5%81%A5%E5%BA%B7%E8%A8%BA%E6%89%80/61586291937168/ | 楊政道、張喬惟、陳韋呈、李苡萍 | 白名單科別：骨科、復健科、風濕免疫科；週日休診 |

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

## 類型 B2：Facebook 固定班表（2 家）— 資料不變，但每月需延伸

| 診所 | Facebook 頁面 | 說明 |
|------|--------------|------|
| c01 禾安復健科 | https://www.facebook.com/share/19qBxvUV52/ | 多年不變，當作固定班表 |
| c12 陳正傑骨科 | https://www.facebook.com/share/1EwsVWdZka/ | 多年不變，當作固定班表 |

**管理原則**：
- 班表內容不變，不需抓取
- 但 sessions 有時間範圍，**每月月初必須延伸到下個月**（和 C3 一起處理）
- 若診所通知班表異動，才需重新截圖並更新內容

**每月延伸操作**（每月 1 日執行）：

1. 依現有固定週班，用 Python 生成下個月整月 sessions
2. 不刪除舊資料，直接新增
3. 執行衝突檢查

參考腳本：`scraper/extend_fixed.py`（處理 B2 + D + C3，每月月初執行一次）

---

## 類型 C1：官方網站月班表（3 家）— 前月月底更新

| 診所 | 網址 | 醫師 | OCR 備註 |
|------|------|------|---------|
| c15 誠陽復健科 | https://sites.google.com/view/chengyang-clinic | 楊景堯、林俊言 | 週三上午僅復健無門診 |
| c16 康澤復健科（土城） | https://kangzereh.com/tuchengkangze#business | 李紹安、許哲維、陳冠誠 | **主表 + 底部 ★ 備註兩層皆須處理** |

### 操作步驟（每月底，抓取下個月班表）

1. 開啟診所網址，找到月班表頁面
2. 截圖，儲存至：
   ```
   scraper/snapshots/web/{診所ID}/YYYYMMDD_schedule.png
   ```
3. 讀取分兩層：
   - **主表格**：固定週班（早/午/晚 × 週一至週六）
   - **底部 ★ 備註欄**：特定日期的代診、停診、時間異動（**不可略過，這是例外資料**）
4. **寫入整月 sessions**：刪除該診所下個月所有舊 sessions，新增整月正確 sessions
   - 先依主表格展開整月，再逐一套用 ★ 備註的例外

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

## 類型 C3：官方網站固定班表（3 家）— 每月檢查

| 診所 | 網址 | 說明 |
|------|------|------|
| c10 板橋維力 | https://www.weili-clinic.com/news/category-5/post-30 | 固定週班（115年），每月確認有無更新 |
| c11 土城維力 | https://www.weili-clinic.com/news/category-5/post-30 | 固定週班（115年），每月確認有無更新 |
| c18 祥明診所 | https://www.shiangming.com/time.php | 固定週班，每月確認有無更新 |

### 操作步驟（每月底）

1. **curl 抓取靜態 HTML**：

```bash
# c10 板橋維力 & c11 土城維力（同一網頁）
curl -s -L "https://www.weili-clinic.com/news/category-5/post-30" \
  > scraper/snapshots/web/c10/YYYYMMDD_html.html
cp scraper/snapshots/web/c10/YYYYMMDD_html.html scraper/snapshots/web/c11/YYYYMMDD_html.html

# c18 祥明診所
curl -s -L "https://www.shiangming.com/time.php" \
  > scraper/snapshots/web/c18/YYYYMMDD_html.html
```

2. **對比上月快照**：若班表無變動，沿用舊 sessions 資料（更新日期即可）
3. 若有變動：重建該診所所有 sessions（刪舊、依新班表補入），記錄變動原因

**sessions 需涵蓋當月 + 下月（約 8 週）**；固定班表每週相同，用 Python 依週期批次生成日期。

#### 板橋維力（c10）＆ 土城維力（c11）說明
- 共用同一網頁：**板橋在上方**，土城在下方
- 2026 起啟用 **115年固定班表**（不再需要每月更新，只需每月確認是否有變動）
- 週六晚上：固定公休

#### 祥明診所（c18）班表摘要（截至 2026-02）
| 診 | 一 | 二 | 三 | 四 | 五 |
|----|----|----|----|----|-----|
| 早 | 黃有明、夏漢詳 | 黃有明、夏漢詳 | 黃有明、楊正楓 | 黃有明 | 黃有明、楊正楓 |
| 午 | 黃有明 | 楊正楓 | 黃有明、夏漢詳 | 楊正楓 | 楊正楓 |
| 晚 | 黃有明 | 楊正楓 | 夏漢詳 | 楊正楓 | 夏漢詳 |

---

## 類型 D：靜態圖片（3 家）— 內容每 6 個月更新，但 sessions 每月延伸

| 診所 | 轉錄文件 | 醫師 |
|------|---------|------|
| c08 正陽骨科 | `scraper/snapshots/image/c08_正陽骨科/schedule_transcription.md` | 蘇哲惟、黃旭東、黃英庭、曾鵯文、蔡馥如 |
| c13 悦滿意永和 | `scraper/snapshots/image/c13_悦滿意永和/schedule_transcription.md` | 悦滿意江、悦滿意李、悦滿意王、悦滿意丁、悦滿意林 |
| c14 悦滿意新店 | `scraper/snapshots/image/c14_悦滿意新店/schedule_transcription.md` | 悦滿意李、悦滿意丁、悦滿意王、悦滿意江、悦滿意羅 |

> ℹ️ 悦滿意醫師命名：圖片只顯示姓氏（「江醫師」），系統統一用「悦滿意江」格式，避免與其他診所同姓醫師混淡。

### D 類型操作說明

**每 6 個月（或診所通知更換時）—更新內容**：

1. 取得新圖片（請診所提供，或從 FB 截圖）
2. 儲存至：`scraper/snapshots/image/{診所ID}_{診所名}/YYYYMMDD_source.png`
3. 人工轉錄，更新 `schedule_transcription.md`
4. 對比 schedules.json，找出差異
5. 更新 schedules.json（卻舊、依新班表補入）

**每月月初—延伸 sessions**：

> 不管內容有沒有變，每月月初都要跟 C3、B2 一起，依現有固定週班延伸到下個月。

1. 依 `schedule_transcription.md` 中的週班，用 Python 生成下個月整月 sessions
2. 不刪除舊資料，直接新增
3. 執行衝突檢查

---

## 類型 E：Vision.com.tw 週班表（1 家）— 每週更新

| 診所 | 網址 | 醫師 whitelist |
|------|------|---------------|
| c24 新店精睿泌尿科 | https://14387.vision.com.tw/Register | 黃旭澤 |

### 技術細節

- 系統：展望亞洲科技 (vision.com.tw)，POST `/Register` 回傳週班表 HTML
- 解析目標：`myFunction('第一診', '黃旭澤', '103', 'uuid', '泌尿科', '日期', '週幾', '時段', ...)`
- **時間偏移**：POST `date=本週一` → 系統回傳**下週**班表（固定偏移 +1 週）
- SSL：vision.com.tw 憑證鏈不完整，爬蟲已停用驗證（`ssl.CERT_NONE`）
- session ID 格式：`jr_{m|a|e}_{MMDD}`（例：`jr_m_0316`）

### 操作步驟（每週日執行）

```bash
# 爬取 c24 未來 5 週班表（輸出到 /tmp 確認內容）
cd /Users/yezuhao/Projects/scraper
python3 scraper/vision_scraper.py --clinic c24 --weeks 5 --output /tmp/jr_sessions.json
```

確認輸出無誤後，將 `/tmp/jr_sessions.json` 的內容合併進 `schedules.json`：

```python
import json

with open('schedules.json', encoding='utf-8') as f:
    sched = json.load(f)

with open('/tmp/jr_sessions.json', encoding='utf-8') as f:
    new_sessions = json.load(f)

# 刪除 c24 舊 sessions，補入新 sessions
sched['sessions'] = [s for s in sched['sessions'] if s['clinic_id'] != 'c24']
sched['sessions'].extend(new_sessions)

with open('schedules.json', 'w', encoding='utf-8') as f:
    json.dump(sched, f, ensure_ascii=False, indent=2)

print(f"✅ c24 更新完成，共 {len(new_sessions)} 筆 sessions")
```

### 特殊注意

- 只追蹤**黃旭澤**，其他醫師（朱信誠、魏汶玲）已由 whitelist 過濾
- 週六有下午門診，**不跳過週六**（與其他診所不同）
- 若系統傳回空白或錯誤，先確認 https://14387.vision.com.tw/Register 是否可連線

---

## 每週執行清單

```
【每週日執行，抓取下週班表】
□ 類型 A（CXMS 8 家）：curl 抓 HTML → Python 解析 → 更新 schedules.json（下週）
□ 類型 C2（永馨 c21）：截圖 → 讀取 → 更新 schedules.json（下週）
□ 類型 E（精睿 c24）：vision_scraper.py --clinic c24 --weeks 5 → 合併 sessions
□ 衝突檢查（見下方）
□ git commit & push

【每月初執行（1日或更新當月第一週前）】
□ 固定班表延伸（以下公用同一支腳本）：
  □ B2（c01 禾安、c12 陳正傑）：依現有週班延伸到下個月
  □ C3（c10 板橋維力、c11 土城維力、c18 祥明）：先檢查有無變動，再延伸
  □ D（c08 正陽、c13 悦滿意永和、c14 悦滿意新店）：依現有週班延伸到下個月
□ git commit & push

【每月底執行（抓取下個月）】
□ 類型 B1（FB 月班表：c09/c17/c22/c23）：截大圖 → 讀取整月 → 新增下月 sessions（不刪本月）
□ 類型 C1（官網月班表：c15/c16）：截圖 → 讀取整月 → 新增下月 sessions（不刪本月）
□ C3 檢查（c10/c11/c18）：對比上月快照，有變動才更新
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
3. 前兩字相同的辨識結果通常可接受（例：滕學淵 vs 滕學澍）

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
├── social/         # Facebook 截圖（c01/c09/c12/c17/c22/c23）
│   └── {診所}/
│       └── YYYYMMDD_schedule_full.png   ← 必須是放大後的全尺寸圖
└── web/            # CXMS + 官方網站截圖
    └── {診所ID}/
        └── YYYYMMDD_schedule.png
```

*最後更新：2026-03-12 v1.7*
