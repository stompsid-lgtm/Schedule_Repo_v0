#!/usr/bin/env python3
"""
社群媒體快照工具 - 適用於 Facebook、LINE VOOM 等社群平台
功能：
1. 使用 Selenium 截圖社群媒體頁面（不嘗試解析 HTML）
2. 快照存於 snapshots/social/{clinic_id}/
3. 產生 metadata JSON（URL、截圖時間、截圖路徑）
4. 人工從截圖轉錄到 schedules.json

社群媒體診所：
  c01 禾安復健科    (Facebook)
  c09 健維骨科      (Facebook)
  c10 板橋維力      (LINE VOOM)
  c12 陳正傑骨科    (Facebook)
  c17 仁祐骨科      (Facebook)
  c22 順安復健科    (Facebook)
  c23 黃石診所      (Facebook)

用法：
  # 對單一診所截圖
  python3 fb_snapshot.py --clinic c01

  # 對所有社群媒體診所截圖
  python3 fb_snapshot.py --all

  # 顯示所有快照狀態
  python3 fb_snapshot.py --status

注意：
  - Facebook 可能需要登入才能看到完整貼文
  - 若截圖顯示登入頁，請改用手動截圖後用 --add-screenshot 加入
  - LINE VOOM 通常不需登入
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

SCRAPER_DIR = Path(__file__).parent
SNAPSHOT_DIR = SCRAPER_DIR / "snapshots" / "social"
SCHEDULES_JSON = SCRAPER_DIR.parent / "schedules.json"

# 社群媒體診所清單
SOCIAL_CLINICS = {
    "c01": {"name": "禾安復健科",   "platform": "facebook"},
    "c09": {"name": "健維骨科",     "platform": "facebook"},
    "c10": {"name": "板橋維力",     "platform": "line_voom"},
    "c12": {"name": "陳正傑骨科",   "platform": "facebook"},
    "c17": {"name": "仁祐骨科",     "platform": "facebook"},
    "c22": {"name": "順安復健科",   "platform": "facebook"},
    "c23": {"name": "黃石診所",     "platform": "facebook"},
}


def load_clinic_urls() -> dict:
    """從 schedules.json 讀取社群媒體診所的 URL"""
    with open(SCHEDULES_JSON, encoding="utf-8") as f:
        data = json.load(f)
    urls = {}
    for c in data["clinics"]:
        if c["id"] in SOCIAL_CLINICS:
            urls[c["id"]] = c.get("source_url", "")
    return urls


def get_clinic_dir(clinic_id: str) -> Path:
    info = SOCIAL_CLINICS.get(clinic_id, {})
    name = info.get("name", clinic_id)
    return SNAPSHOT_DIR / f"{clinic_id}_{name}"


def take_screenshot(clinic_id: str, url: str, clinic_name: str, platform: str) -> dict:
    """
    使用 Selenium 截圖社群媒體頁面
    回傳快照結果 dict
    """
    clinic_dir = get_clinic_dir(clinic_id)
    clinic_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = {
        "clinic_id": clinic_id,
        "clinic_name": clinic_name,
        "platform": platform,
        "url": url,
        "date_str": date_str,
        "screenshot_file": None,
        "meta_file": None,
        "success": False,
        "error": None,
        "needs_login": False,
    }

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1280,900")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )

        driver = webdriver.Chrome(options=options)
        try:
            print(f"  🌐 開啟 {url} ...")
            driver.get(url)
            time.sleep(4)  # 等待頁面載入

            # 偵測是否被導向登入頁
            current_url = driver.current_url
            if any(kw in current_url.lower() for kw in ["login", "checkpoint"]):
                result["needs_login"] = True
                print(f"  ⚠️  {clinic_name}: 被導向登入頁")

            # 嘗試關閉 Facebook 登入 modal（按 Escape）
            try:
                driver.find_element("tag name", "body").send_keys(Keys.ESCAPE)
                time.sleep(1.5)
            except Exception:
                pass

            # 向下滾動讓班表圖片進入視野
            driver.execute_script("window.scrollBy(0, 400);")
            time.sleep(1)

            # 截圖
            screenshot_file = clinic_dir / f"{date_str}_screenshot.png"
            driver.save_screenshot(str(screenshot_file))
            result["screenshot_file"] = str(screenshot_file)
            result["success"] = True

            print(f"  ✅ {clinic_name}: 截圖已儲存")
            print(f"     → {screenshot_file}")
            if result["needs_login"]:
                print(f"     ⚠️  需要登入，請手動截圖並用 --add-screenshot 加入")

        finally:
            driver.quit()

    except ImportError:
        result["error"] = "selenium 未安裝，請執行: pip3 install selenium"
        print(f"  ❌ {clinic_name}: {result['error']}")
    except Exception as e:
        result["error"] = str(e)
        print(f"  ❌ {clinic_name}: {e}")

    # 儲存 metadata（無論截圖是否成功）
    meta = {
        "clinic_id": clinic_id,
        "clinic_name": clinic_name,
        "platform": platform,
        "url": url,
        "snapshot_at": datetime.now().isoformat(),
        "screenshot_file": result.get("screenshot_file"),
        "success": result["success"],
        "needs_login": result.get("needs_login", False),
        "error": result.get("error"),
        "transcribed": False,  # 人工轉錄後改為 True
        "transcription_notes": "",
    }
    meta_file = clinic_dir / f"{date_str}_meta.json"
    meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    result["meta_file"] = str(meta_file)

    return result


def add_screenshot_manually(clinic_id: str, screenshot_path: str, note: str = ""):
    """手動加入截圖（當自動截圖失敗時使用）"""
    import shutil

    if clinic_id not in SOCIAL_CLINICS:
        print(f"❌ 未知診所 ID: {clinic_id}")
        return

    info = SOCIAL_CLINICS[clinic_id]
    src = Path(screenshot_path)
    if not src.exists():
        print(f"❌ 找不到截圖: {screenshot_path}")
        return

    clinic_dir = get_clinic_dir(clinic_id)
    clinic_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = clinic_dir / f"{date_str}_manual_{src.name}"
    shutil.copy2(src, dest)

    meta = {
        "clinic_id": clinic_id,
        "clinic_name": info["name"],
        "platform": info["platform"],
        "snapshot_at": datetime.now().isoformat(),
        "screenshot_file": str(dest),
        "source": "manual",
        "notes": note,
        "transcribed": False,
        "transcription_notes": "",
    }
    meta_file = clinic_dir / f"{date_str}_manual_meta.json"
    meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ 手動截圖已加入: {dest}")


def mark_transcribed(clinic_id: str, note: str = ""):
    """標記最新快照已完成人工轉錄"""
    clinic_dir = get_clinic_dir(clinic_id)
    if not clinic_dir.exists():
        print(f"❌ 找不到診所目錄: {clinic_dir}")
        return

    # 找最新的 meta.json
    meta_files = sorted(clinic_dir.glob("*_meta.json"), reverse=True)
    if not meta_files:
        print(f"❌ 找不到 meta.json")
        return

    latest_meta = meta_files[0]
    meta = json.loads(latest_meta.read_text(encoding="utf-8"))
    meta["transcribed"] = True
    meta["transcription_notes"] = note
    meta["transcribed_at"] = datetime.now().isoformat()
    latest_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ {SOCIAL_CLINICS.get(clinic_id, {}).get('name', clinic_id)}: 已標記轉錄完成")


def show_status():
    """顯示所有社群媒體診所的快照狀態"""
    print("\n📱 社群媒體診所快照狀態\n")
    print(f"{'診所':12} {'平台':10} {'最新快照':20} {'截圖':6} {'已轉錄':6} {'備註'}")
    print("-" * 75)

    for clinic_id, info in SOCIAL_CLINICS.items():
        clinic_dir = get_clinic_dir(clinic_id)
        if not clinic_dir.exists():
            print(f"  {info['name']:10} {info['platform']:10} {'❌ 無快照':20}")
            continue

        meta_files = sorted(clinic_dir.glob("*_meta.json"), reverse=True)
        if not meta_files:
            print(f"  {info['name']:10} {info['platform']:10} {'❌ 無快照':20}")
            continue

        latest = json.loads(meta_files[0].read_text(encoding="utf-8"))
        snapshot_at = latest.get("snapshot_at", "")[:16].replace("T", " ")
        has_screenshot = "✅" if latest.get("screenshot_file") and Path(latest.get("screenshot_file", "")).exists() else "❌"
        transcribed = "✅" if latest.get("transcribed") else "⏳"
        notes = latest.get("transcription_notes", "")[:20]

        print(f"  {info['name']:10} {info['platform']:10} {snapshot_at:20} {has_screenshot:6} {transcribed:6} {notes}")

    print()


def run_all():
    """對所有社群媒體診所截圖"""
    urls = load_clinic_urls()
    print(f"\n📸 開始對 {len(SOCIAL_CLINICS)} 個社群媒體診所截圖...\n")
    results = []
    for clinic_id, info in SOCIAL_CLINICS.items():
        url = urls.get(clinic_id, "")
        if not url:
            print(f"  ⚠️  {info['name']}: 找不到 URL，跳過")
            continue
        r = take_screenshot(clinic_id, url, info["name"], info["platform"])
        results.append(r)
        time.sleep(3)

    success = sum(1 for r in results if r["success"])
    needs_login = sum(1 for r in results if r.get("needs_login"))
    print(f"\n✨ 完成: {success}/{len(results)} 截圖成功, {needs_login} 個需要登入")
    if needs_login > 0:
        print("   ⚠️  需要登入的診所請手動截圖，再用 --add-screenshot 加入")
    return results


def main():
    parser = argparse.ArgumentParser(description="社群媒體快照工具")
    parser.add_argument("--status", action="store_true", help="顯示所有快照狀態")
    parser.add_argument("--all", action="store_true", help="對所有社群媒體診所截圖")
    parser.add_argument("--clinic", metavar="CLINIC_ID", help="指定診所 (例如 c01)")
    parser.add_argument("--add-screenshot", metavar="IMAGE_PATH", help="手動加入截圖")
    parser.add_argument("--mark-transcribed", action="store_true", help="標記最新快照已轉錄")
    parser.add_argument("--note", default="", help="備註")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.all:
        run_all()
    elif args.add_screenshot and args.clinic:
        add_screenshot_manually(args.clinic, args.add_screenshot, note=args.note)
    elif args.mark_transcribed and args.clinic:
        mark_transcribed(args.clinic, note=args.note)
    elif args.clinic:
        urls = load_clinic_urls()
        info = SOCIAL_CLINICS.get(args.clinic)
        if not info:
            print(f"❌ 未知診所 ID: {args.clinic}")
            return
        url = urls.get(args.clinic, "")
        if not url:
            print(f"❌ 找不到 URL for {args.clinic}")
            return
        take_screenshot(args.clinic, url, info["name"], info["platform"])
    else:
        show_status()


if __name__ == "__main__":
    main()
