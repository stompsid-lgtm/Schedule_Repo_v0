# 診所排班資料爬蟲與驗證工具

## 📁 目錄結構

```
scraper/
├── web_validator.py      # CXMS 網站爬取 + 反爬蟲偵測 + HTML 快照
├── fb_snapshot.py        # Facebook / LINE VOOM 截圖快照
├── image_validator.py    # 圖片來源驗證記錄管理
├── weili_scraper.py      # 維力骨科爬蟲（Selenium）
├── weili_data.py         # 維力骨科固定班表資料
├── requirements.txt      # Python 依賴
└── snapshots/
    ├── image/            # 圖片來源快照（正陽、悅滿意）
    ├── web/              # 網站來源快照（CXMS 等）
    └── social/           # 社群媒體快照（FB、LINE VOOM）
```

---

## 🗂️ 資料來源分類（22 家診所）

| 類型 | 診所 | 驗證工具 |
|------|------|---------|
| 🖼️ **圖片** | 正陽(c08)、悅滿意永和(c13)、悅滿意新店(c14) | `image_validator.py` |
| 🌐 **CXMS 網站** | 維恩(c02)、富新(c03)、得安(c04)、昌惟(c05)、昌禾(c06)、土城杏光(c07)、得揚(c19)、力康(c20) | `web_validator.py` |
| 📘 **Facebook** | 禾安(c01)、健維(c09)、陳正傑(c12)、仁祐(c17)、順安(c22) | `fb_snapshot.py` |
| 🔗 **其他網站** | 板橋維力(c10, LINE VOOM)、土城維力(c11)、誠陽(c15)、康澤(c16)、祥明(c18)、永馨(c21) | `web_validator.py` / `fb_snapshot.py` |

---

## 🚀 安裝依賴

```bash
cd scraper
pip3 install -r requirements.txt
```

> Chrome + ChromeDriver 需另外安裝（用於 Selenium 截圖）：
> ```bash
> brew install chromedriver
> ```

---

## 🌐 CXMS 網站驗證（`web_validator.py`）

**反爬蟲偵測結果（2026-02-18）：8/8 全部可直接爬取，無 Cloudflare，無需 JS 渲染。**

```bash
# 反爬蟲偵測（不儲存快照）
python3 scraper/web_validator.py --check-only

# 對單一診所建立 HTML 快照
python3 scraper/web_validator.py --clinic c02

# 對所有 CXMS 診所建立快照
python3 scraper/web_validator.py --all-cxms
```

快照儲存於 `snapshots/web/{clinic_id}/`，每次包含：
- `{timestamp}_html.html` — 完整 HTML
- `{timestamp}_meta.json` — 爬取 metadata

---

## 🖼️ 圖片來源驗證（`image_validator.py`）

圖片班表更新頻率極低，只需確保初次轉錄正確，每 6 個月複查一次。

```bash
# 查看所有圖片診所的驗證狀態
python3 scraper/image_validator.py --status

# 初始化驗證目錄（首次使用）
python3 scraper/image_validator.py --init c08

# 將圖片加入快照目錄
python3 scraper/image_validator.py --add-image /path/to/schedule.jpg --clinic c08

# 確認轉錄正確後標記
python3 scraper/image_validator.py --update c08 --note "已對照圖片確認，無誤"
```

---

## 📱 社群媒體快照（`fb_snapshot.py`）

Facebook / LINE VOOM 不嘗試自動解析，只截圖供人工轉錄。

```bash
# 查看所有社群媒體診所的快照狀態
python3 scraper/fb_snapshot.py --status

# 對單一診所截圖
python3 scraper/fb_snapshot.py --clinic c01

# 對所有社群媒體診所截圖
python3 scraper/fb_snapshot.py --all

# 手動加入截圖（當自動截圖失敗時）
python3 scraper/fb_snapshot.py --add-screenshot /path/to/screenshot.png --clinic c01 --note "手動截圖"

# 標記已完成人工轉錄
python3 scraper/fb_snapshot.py --mark-transcribed --clinic c01 --note "已更新 schedules.json"
```

> ⚠️ **Facebook 注意**：部分貼文需要登入才能看到，若截圖顯示登入頁，請手動截圖後用 `--add-screenshot` 加入。

---

## 📋 每週更新流程

1. **CXMS 診所**（自動）：
   ```bash
   python3 scraper/web_validator.py --all-cxms
   # 對照 HTML 快照更新 schedules.json
   ```

2. **圖片診所**（每 6 個月複查）：
   ```bash
   python3 scraper/image_validator.py --status
   # 若有到期，重新確認圖片
   ```

3. **社群媒體診所**（手動）：
   ```bash
   python3 scraper/fb_snapshot.py --all
   # 對照截圖更新 schedules.json
   python3 scraper/fb_snapshot.py --mark-transcribed --clinic c01
   ```

4. **部署更新**：
   ```bash
   git add schedules.json
   git commit -m "Update schedule: YYYY-MM-DD week"
   git push
   ```
