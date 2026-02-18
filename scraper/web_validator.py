#!/usr/bin/env python3
"""
網站資料驗證器 - 適用於 CXMS 及其他網站來源
功能：
1. 反爬蟲偵測（robots.txt、Cloudflare、JS 渲染需求）
2. 爬取時同步建立快照（HTML + 截圖 + 提取結果）
3. 快照存於 snapshots/web/{clinic_id}/

用法：
  # 只做反爬蟲偵測
  python3 web_validator.py --check-only

  # 對單一診所截圖快照
  python3 web_validator.py --clinic c02

  # 對所有 CXMS 診所做快照
  python3 web_validator.py --all-cxms

  # 對指定 URL 做快照（不需要 clinic_id）
  python3 web_validator.py --url http://web.cxms.com.tw/wn/hosp.php --clinic c02
"""

import argparse
import json
import time
import urllib.request
import urllib.robotparser
from datetime import datetime
from pathlib import Path

SCRAPER_DIR = Path(__file__).parent
SNAPSHOT_DIR = SCRAPER_DIR / "snapshots" / "web"
SCHEDULES_JSON = SCRAPER_DIR.parent / "schedules.json"

# CXMS 診所清單（從 schedules.json 讀取）
CXMS_CLINICS = {}

def load_cxms_clinics():
    """從 schedules.json 讀取 CXMS 診所"""
    global CXMS_CLINICS
    with open(SCHEDULES_JSON, encoding="utf-8") as f:
        data = json.load(f)
    for c in data["clinics"]:
        url = c.get("source_url", "")
        if "cxms.com.tw" in url:
            CXMS_CLINICS[c["id"]] = {
                "name": c["name"],
                "url": url,
            }
    return CXMS_CLINICS


def check_robots_txt(base_url: str) -> dict:
    """檢查 robots.txt 是否允許爬取"""
    result = {"allowed": True, "robots_url": "", "error": None}
    try:
        # 取得 base URL
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        result["robots_url"] = robots_url

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        result["allowed"] = rp.can_fetch("*", base_url)
    except Exception as e:
        result["error"] = str(e)
        result["allowed"] = True  # 無法讀取時預設允許
    return result


def check_anti_scraping(url: str, clinic_name: str = "") -> dict:
    """
    偵測反爬蟲機制
    回傳：
      - status_code: HTTP 狀態碼
      - has_cloudflare: 是否有 Cloudflare
      - needs_js: 是否需要 JS 渲染（頁面內容極少）
      - robots_ok: robots.txt 是否允許
      - response_size: 回應大小（bytes）
      - accessible: 是否可存取
    """
    result = {
        "clinic": clinic_name,
        "url": url,
        "status_code": None,
        "has_cloudflare": False,
        "needs_js": False,
        "robots_ok": True,
        "response_size": 0,
        "accessible": False,
        "error": None,
        "checked_at": datetime.now().isoformat(),
    }

    # 1. 檢查 robots.txt
    robots = check_robots_txt(url)
    result["robots_ok"] = robots["allowed"]
    if not robots["allowed"]:
        print(f"  ⚠️  robots.txt 不允許爬取: {url}")

    # 2. 發送 HTTP 請求
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            result["status_code"] = resp.status
            content = resp.read()
            result["response_size"] = len(content)
            html = content.decode("utf-8", errors="replace")

            # 偵測 Cloudflare
            if any(kw in html for kw in ["cloudflare", "cf-ray", "__cf_bm", "Checking your browser"]):
                result["has_cloudflare"] = True

            # 偵測是否需要 JS（頁面內容極少）
            if len(html) < 500:
                result["needs_js"] = True
            elif "<table" not in html.lower() and "<div" not in html.lower():
                result["needs_js"] = True

            result["accessible"] = True
            result["_html_preview"] = html[:300]  # 前 300 字元供除錯

    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        result["error"] = f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        result["error"] = str(e)

    return result


def scrape_with_snapshot(url: str, clinic_id: str, clinic_name: str = "") -> dict:
    """
    爬取網頁並建立快照
    快照內容：
      - {date}_html.html     完整 HTML
      - {date}_meta.json     爬取 metadata（URL、時間、狀態）
    注意：截圖需要 Selenium，此函數先做 HTML 快照
    """
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    clinic_dir = SNAPSHOT_DIR / clinic_id
    clinic_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "clinic_id": clinic_id,
        "clinic_name": clinic_name,
        "url": url,
        "snapshot_dir": str(clinic_dir),
        "date_str": date_str,
        "html_file": None,
        "meta_file": None,
        "success": False,
        "error": None,
    }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            html = content.decode("utf-8", errors="replace")

        # 儲存 HTML 快照
        html_file = clinic_dir / f"{date_str}_html.html"
        html_file.write_text(html, encoding="utf-8")
        result["html_file"] = str(html_file)

        # 儲存 metadata
        meta = {
            "clinic_id": clinic_id,
            "clinic_name": clinic_name,
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "html_file": str(html_file),
            "html_size_bytes": len(content),
            "status": "success",
        }
        meta_file = clinic_dir / f"{date_str}_meta.json"
        meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        result["meta_file"] = str(meta_file)
        result["success"] = True

        print(f"  ✅ {clinic_name}: HTML 快照已儲存 ({len(content):,} bytes)")
        print(f"     → {html_file}")

    except Exception as e:
        result["error"] = str(e)
        print(f"  ❌ {clinic_name}: 爬取失敗 - {e}")

    return result


def run_check_only():
    """只做反爬蟲偵測，不儲存快照"""
    clinics = load_cxms_clinics()
    print(f"\n🔍 反爬蟲偵測 - {len(clinics)} 個 CXMS 診所\n")
    print(f"{'診所':12} {'狀態碼':8} {'CF':5} {'需JS':6} {'robots':7} {'大小':10} {'說明'}")
    print("-" * 70)

    results = []
    for clinic_id, info in clinics.items():
        print(f"  檢查 {info['name']} ({info['url']})...")
        r = check_anti_scraping(info["url"], info["name"])
        results.append(r)

        status = r.get("status_code", "ERR")
        cf = "⚠️" if r["has_cloudflare"] else "✅"
        js = "⚠️" if r["needs_js"] else "✅"
        robots = "✅" if r["robots_ok"] else "⚠️"
        size = f"{r['response_size']:,}" if r["response_size"] else "—"
        note = r.get("error", "OK") or "OK"

        print(f"  {info['name']:10} {str(status):8} {cf:5} {js:6} {robots:7} {size:10} {note[:30]}")
        time.sleep(1)  # 避免過快請求

    # 儲存偵測結果
    report_file = SCRAPER_DIR / f"anti_scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📄 報告已儲存: {report_file}")

    # 摘要
    accessible = sum(1 for r in results if r["accessible"])
    has_cf = sum(1 for r in results if r["has_cloudflare"])
    needs_js = sum(1 for r in results if r["needs_js"])
    print(f"\n📊 摘要: {accessible}/{len(results)} 可存取, {has_cf} 有CF, {needs_js} 需JS渲染")

    return results


def run_snapshot(clinic_id: str = None, url: str = None):
    """對指定診所或 URL 做快照"""
    clinics = load_cxms_clinics()

    if clinic_id and clinic_id in clinics:
        info = clinics[clinic_id]
        result = scrape_with_snapshot(info["url"], clinic_id, info["name"])
    elif url and clinic_id:
        result = scrape_with_snapshot(url, clinic_id, clinic_id)
    else:
        print("❌ 請指定 --clinic 或同時指定 --url 和 --clinic")
        return

    return result


def run_all_cxms_snapshots():
    """對所有 CXMS 診所做快照"""
    clinics = load_cxms_clinics()
    print(f"\n📸 開始對 {len(clinics)} 個 CXMS 診所建立快照...\n")
    results = []
    for clinic_id, info in clinics.items():
        r = scrape_with_snapshot(info["url"], clinic_id, info["name"])
        results.append(r)
        time.sleep(2)  # 避免過快請求

    success = sum(1 for r in results if r["success"])
    print(f"\n✨ 完成: {success}/{len(results)} 成功")
    return results


def main():
    parser = argparse.ArgumentParser(description="網站資料驗證器")
    parser.add_argument("--check-only", action="store_true", help="只做反爬蟲偵測")
    parser.add_argument("--clinic", help="診所 ID (例如 c02)")
    parser.add_argument("--url", help="指定 URL")
    parser.add_argument("--all-cxms", action="store_true", help="對所有 CXMS 診所做快照")
    args = parser.parse_args()

    if args.check_only:
        run_check_only()
    elif args.all_cxms:
        run_all_cxms_snapshots()
    elif args.clinic or args.url:
        run_snapshot(clinic_id=args.clinic, url=args.url)
    else:
        # 預設：先做偵測
        print("未指定模式，執行反爬蟲偵測...")
        run_check_only()


if __name__ == "__main__":
    main()
