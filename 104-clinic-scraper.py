#!/usr/bin/env python3
"""
104 新成立診所爬蟲
搜尋台北市+新北市新成立/籌備中的診所，排除指定科別

用法:
  python3 104-clinic-scraper.py                  # 預設搜尋
  python3 104-clinic-scraper.py --out results.json  # 輸出 JSON
"""

import json
import urllib.request
import urllib.parse
import argparse
from collections import defaultdict
from datetime import datetime

# ── 設定 ──────────────────────────────────────────────────

API_URL = "https://www.104.com.tw/jobs/search/api/jobs"

HEADERS = {
    "Referer": "https://www.104.com.tw/jobs/search/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

# 區域代碼
AREAS = {
    "台北市": "6001001000",
    "新北市": "6001002000",
}

# API 層級排除（職缺內容/標題）
API_EXCLUDE = "牙科,眼科,兒科,皮膚科,醫美,中醫"

# Post-filter 排除（公司名比對）
NAME_EXCLUDE_KEYWORDS = [
    "牙", "眼科", "兒科", "皮膚", "醫美", "中醫",
    "美學", "美容", "婦產", "產後", "月子",
]

# 多策略搜尋關鍵字
SEARCH_STRATEGIES = [
    # (keyword, extra_params, 說明)
    ("診所（籌備處）", {}, "公司名含籌備處"),
    ("診所(籌備處)", {}, "公司名含籌備處(半形)"),
    ("籌備", {"indcat": "1012001002"}, "診所產業+籌備"),
    ("新成立", {"indcat": "1012001002"}, "診所產業+新成立"),
    ("新開幕", {"indcat": "1012001002"}, "診所產業+新開幕"),
    ("即將開幕", {"indcat": "1012001002"}, "診所產業+即將開幕"),
]


# ── 核心函式 ──────────────────────────────────────────────

def fetch_page(params: dict) -> dict:
    """打 104 API 拿一頁結果"""
    qs = urllib.parse.urlencode(params)
    url = f"{API_URL}?{qs}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def fetch_all_pages(params_base: dict) -> list:
    """自動翻頁，回傳所有 job list"""
    all_jobs = []
    for page in range(1, 50):
        params_base["page"] = str(page)
        d = fetch_page(params_base)
        pagination = d.get("metadata", {}).get("pagination", {})
        data = d.get("data", {})
        lst = data.get("list", []) if isinstance(data, dict) else data
        all_jobs.extend(lst)
        if page >= pagination.get("lastPage", 1):
            break
    return all_jobs


def is_name_excluded(name: str) -> bool:
    """公司名是否命中排除關鍵字"""
    return any(kw in name for kw in NAME_EXCLUDE_KEYWORDS)


def is_relevant(job: dict) -> bool:
    """判斷這筆 job 是否跟新成立診所相關（非泛用診所職缺）"""
    name = job.get("custName", "")
    title = job.get("jobName", "")
    desc = job.get("description", "")
    combined = name + title + desc

    relevance_keywords = ["籌備", "新成立", "新開幕", "即將開幕", "開幕", "籌設"]
    return any(kw in combined for kw in relevance_keywords)


def run_scraper(areas: dict) -> list:
    """執行多策略搜尋，合併去重 + post-filter"""
    area_codes = ",".join(areas.values())
    seen_job_nos = set()
    all_jobs = []

    for keyword, extra_params, label in SEARCH_STRATEGIES:
        params = {
            "keyword": keyword,
            "area": area_codes,
            "order": "15",
            "mode": "s",
            "excludeJobKeyword": API_EXCLUDE,
            **extra_params,
        }
        jobs = fetch_all_pages(params)
        new_count = 0
        for j in jobs:
            jno = j.get("jobNo", "")
            if jno and jno not in seen_job_nos:
                seen_job_nos.add(jno)
                all_jobs.append(j)
                new_count += 1
        print(f"  [{label}] {len(jobs)} 筆，新增 {new_count} 筆")

    print(f"\n合併去重: {len(all_jobs)} 筆")

    # Post-filter: 排除科別
    filtered = [j for j in all_jobs if not is_name_excluded(j.get("custName", ""))]
    excluded_count = len(all_jobs) - len(filtered)
    print(f"排除不符科別: -{excluded_count} 筆")

    # Post-filter: 只保留跟「新成立」相關的
    relevant = [j for j in filtered if is_relevant(j)]
    noise_count = len(filtered) - len(relevant)
    print(f"排除無關職缺: -{noise_count} 筆")
    print(f"最終結果: {len(relevant)} 筆")

    return relevant


def group_by_company(jobs: list) -> dict:
    """按公司名分組"""
    groups = defaultdict(list)
    for j in jobs:
        groups[j.get("custName", "")].append(j)
    return dict(groups)


def print_results(groups: dict):
    """印出結果"""
    print(f"\n{'=' * 90}")
    print(f"共 {len(groups)} 家診所")
    print(f"{'=' * 90}")

    for company in sorted(groups.keys()):
        jobs = groups[company]
        addr = (jobs[0].get("jobAddrNoDesc", "") + " " + jobs[0].get("jobAddress", "")).strip()
        link = jobs[0].get("link", {}).get("job", "")
        if link and not link.startswith("http"):
            link = "https:" + link
        appear = jobs[0].get("appearDate", "")

        tag = "🏗️" if "籌備" in company else "🆕"
        print(f"\n{tag} {company}")
        print(f"   📍 {addr}")
        print(f"   🔗 {link}")
        print(f"   📅 {appear}")
        print(f"   職缺 ({len(jobs)}):")
        for j in jobs:
            salary_desc = j.get("salaryDesc", "")
            title = j.get("jobName", "")
            line = f"     - {title}"
            if salary_desc:
                line += f"  [{salary_desc}]"
            print(line)


def export_json(groups: dict, path: str):
    """匯出 JSON"""
    output = []
    for company in sorted(groups.keys()):
        jobs = groups[company]
        link = jobs[0].get("link", {}).get("job", "")
        if link and not link.startswith("http"):
            link = "https:" + link
        output.append({
            "company": company,
            "address": (jobs[0].get("jobAddrNoDesc", "") + " " + jobs[0].get("jobAddress", "")).strip(),
            "link": link,
            "appear_date": jobs[0].get("appearDate", ""),
            "is_prep": "籌備" in company,
            "positions": [
                {
                    "title": j.get("jobName", ""),
                    "salary": j.get("salaryDesc", ""),
                    "job_url": ("https:" + j["link"]["job"]) if j.get("link", {}).get("job", "").startswith("//") else j.get("link", {}).get("job", ""),
                }
                for j in jobs
            ],
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n💾 已匯出 → {path}")


# ── Main ──────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="104 新成立診所爬蟲")
    parser.add_argument("--out", type=str, help="匯出 JSON 檔路徑")
    args = parser.parse_args()

    print(f"🔍 104 新成立診所爬蟲 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   區域: {', '.join(AREAS.keys())}")
    print(f"   排除: {', '.join(NAME_EXCLUDE_KEYWORDS)}")
    print()

    jobs = run_scraper(AREAS)
    groups = group_by_company(jobs)
    print_results(groups)

    if args.out:
        export_json(groups, args.out)
