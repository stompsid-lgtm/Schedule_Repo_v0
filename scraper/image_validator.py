#!/usr/bin/env python3
"""
圖片資料驗證器 - 適用於靜態圖片來源（正陽骨科、悅滿意永和/新店）
功能：
1. 建立圖片快照目錄與驗證記錄
2. 產生 verified.json（轉錄驗證記錄）
3. 提醒下次複查日期

圖片來源診所：
  c08 正陽骨科
  c13 悅滿意永和
  c14 悅滿意新店

用法：
  # 列出所有圖片診所的驗證狀態
  python3 image_validator.py --status

  # 為指定診所建立驗證記錄（人工填寫後執行）
  python3 image_validator.py --init c08

  # 更新驗證記錄（重新轉錄後執行）
  python3 image_validator.py --update c08 --note "重新確認班表，無變動"
"""

import argparse
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

SCRAPER_DIR = Path(__file__).parent
SNAPSHOT_DIR = SCRAPER_DIR / "snapshots" / "image"
SCHEDULES_JSON = SCRAPER_DIR.parent / "schedules.json"

# 圖片來源診所
IMAGE_CLINICS = {
    "c08": {"name": "正陽骨科", "review_interval_days": 180},
    "c13": {"name": "悅滿意永和", "review_interval_days": 180},
    "c14": {"name": "悅滿意新店", "review_interval_days": 180},
}


def get_clinic_dir(clinic_id: str) -> Path:
    info = IMAGE_CLINICS.get(clinic_id, {})
    name = info.get("name", clinic_id)
    safe_name = name.replace("/", "_").replace(" ", "_")
    return SNAPSHOT_DIR / f"{clinic_id}_{safe_name}"


def get_verified_path(clinic_id: str) -> Path:
    return get_clinic_dir(clinic_id) / "verified.json"


def init_clinic(clinic_id: str):
    """初始化診所的圖片驗證目錄"""
    if clinic_id not in IMAGE_CLINICS:
        print(f"❌ 未知診所 ID: {clinic_id}，可用: {list(IMAGE_CLINICS.keys())}")
        return

    info = IMAGE_CLINICS[clinic_id]
    clinic_dir = get_clinic_dir(clinic_id)
    clinic_dir.mkdir(parents=True, exist_ok=True)

    verified_path = get_verified_path(clinic_id)
    if verified_path.exists():
        print(f"⚠️  {info['name']} 已有驗證記錄: {verified_path}")
        print("   使用 --update 來更新記錄")
        return

    # 建立初始驗證記錄
    now = datetime.now()
    next_review = now + timedelta(days=info["review_interval_days"])
    record = {
        "clinic_id": clinic_id,
        "clinic_name": info["name"],
        "source_type": "image",
        "transcribed_at": now.isoformat(),
        "transcribed_by": "manual",
        "verified": False,  # 初始為未驗證，人工確認後改為 True
        "notes": "",
        "image_files": [],  # 填入圖片檔名
        "next_review_date": next_review.strftime("%Y-%m-%d"),
        "review_interval_days": info["review_interval_days"],
        "history": []
    }

    verified_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已建立驗證目錄: {clinic_dir}")
    print(f"   驗證記錄: {verified_path}")
    print(f"\n📋 下一步：")
    print(f"   1. 將原始圖片複製到 {clinic_dir}/")
    print(f"   2. 對照圖片確認 schedules.json 中的資料正確")
    print(f"   3. 執行: python3 image_validator.py --update {clinic_id} --note '已確認'")


def update_clinic(clinic_id: str, note: str = "", verified: bool = True):
    """更新診所的驗證記錄"""
    if clinic_id not in IMAGE_CLINICS:
        print(f"❌ 未知診所 ID: {clinic_id}")
        return

    info = IMAGE_CLINICS[clinic_id]
    verified_path = get_verified_path(clinic_id)

    if not verified_path.exists():
        print(f"❌ 找不到驗證記錄，請先執行: python3 image_validator.py --init {clinic_id}")
        return

    record = json.loads(verified_path.read_text(encoding="utf-8"))

    # 加入歷史記錄
    history_entry = {
        "date": datetime.now().isoformat(),
        "verified": record.get("verified"),
        "notes": record.get("notes"),
    }
    record.setdefault("history", []).append(history_entry)

    # 更新記錄
    now = datetime.now()
    next_review = now + timedelta(days=info["review_interval_days"])
    record["transcribed_at"] = now.isoformat()
    record["verified"] = verified
    record["notes"] = note
    record["next_review_date"] = next_review.strftime("%Y-%m-%d")

    # 掃描目錄中的圖片
    clinic_dir = get_clinic_dir(clinic_id)
    image_files = [f.name for f in clinic_dir.iterdir()
                   if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif")]
    record["image_files"] = sorted(image_files)

    verified_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    status = "✅ 已驗證" if verified else "⚠️ 待驗證"
    print(f"{status} {info['name']} 驗證記錄已更新")
    print(f"   下次複查日期: {record['next_review_date']}")


def show_status():
    """顯示所有圖片診所的驗證狀態"""
    print("\n🖼️  圖片來源診所驗證狀態\n")
    print(f"{'診所':12} {'狀態':8} {'最後驗證':12} {'下次複查':12} {'圖片數':6} {'備註'}")
    print("-" * 75)

    today = datetime.now().date()
    for clinic_id, info in IMAGE_CLINICS.items():
        verified_path = get_verified_path(clinic_id)
        if not verified_path.exists():
            print(f"  {info['name']:10} {'❌ 未初始化':10} {'—':12} {'—':12} {'—':6}")
            continue

        record = json.loads(verified_path.read_text(encoding="utf-8"))
        verified = "✅ 已驗證" if record.get("verified") else "⚠️ 待確認"
        transcribed = record.get("transcribed_at", "")[:10]
        next_review = record.get("next_review_date", "")
        img_count = len(record.get("image_files", []))
        notes = record.get("notes", "")[:20]

        # 複查提醒
        if next_review:
            next_dt = datetime.strptime(next_review, "%Y-%m-%d").date()
            days_left = (next_dt - today).days
            if days_left < 0:
                next_review = f"{next_review} ⚠️ 已過期"
            elif days_left < 30:
                next_review = f"{next_review} ⚠️ {days_left}天後"

        print(f"  {info['name']:10} {verified:10} {transcribed:12} {next_review:20} {img_count:<6} {notes}")

    print()


def add_image(clinic_id: str, image_path: str):
    """將圖片複製到快照目錄"""
    if clinic_id not in IMAGE_CLINICS:
        print(f"❌ 未知診所 ID: {clinic_id}")
        return

    src = Path(image_path)
    if not src.exists():
        print(f"❌ 找不到圖片: {image_path}")
        return

    clinic_dir = get_clinic_dir(clinic_id)
    clinic_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    dest = clinic_dir / f"{date_str}_{src.name}"
    shutil.copy2(src, dest)
    print(f"✅ 圖片已複製: {dest}")


def main():
    parser = argparse.ArgumentParser(description="圖片資料驗證器")
    parser.add_argument("--status", action="store_true", help="顯示所有圖片診所的驗證狀態")
    parser.add_argument("--init", metavar="CLINIC_ID", help="初始化診所驗證目錄 (例如 c08)")
    parser.add_argument("--update", metavar="CLINIC_ID", help="更新驗證記錄")
    parser.add_argument("--note", default="", help="驗證備註")
    parser.add_argument("--unverified", action="store_true", help="標記為未驗證（與 --update 搭配）")
    parser.add_argument("--add-image", metavar="IMAGE_PATH", help="新增圖片到快照目錄")
    parser.add_argument("--clinic", metavar="CLINIC_ID", help="指定診所（與 --add-image 搭配）")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.init:
        init_clinic(args.init)
    elif args.update:
        update_clinic(args.update, note=args.note, verified=not args.unverified)
    elif args.add_image and args.clinic:
        add_image(args.clinic, args.add_image)
    else:
        show_status()


if __name__ == "__main__":
    main()
