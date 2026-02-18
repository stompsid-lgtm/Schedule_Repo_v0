"""
根據已知的門診表圖片，手動建立兩間維力骨科的固定資料
這個檔案可以直接整合到 schedules.json 中
"""

weili_clinics_data = {
    "tucheng_weili": {
        "clinic_id": "土城維力",
        "name": "土城維力骨科診所",
        "color": "#2563eb",  # 藍色
        "source_url": "https://www.weili-clinic.com/news/category-5/post-30",
        "whitelist": ["劉大維", "張晉顥"],  # 重點醫師
        "blacklist": [],
        "fixed_schedule": True,  # 標記為固定班表
        "schedule": {
            # 固定班表115年~
            "MON": {
                "morning": ["劉大維"],
                "afternoon": ["劉大維"],
                "evening": ["張晉顥"]
            },
            "TUE": {
                "morning": ["張晉顥"],
                "afternoon": ["張晉顥"],
                "evening": ["劉大維"]
            },
            "WED": {
                "morning": ["劉大維"],
                "afternoon": ["楊欣諭"],
                "evening": ["楊欣諭"]
            },
            "THU": {
                "morning": ["楊欣諭"],
                "afternoon": ["劉大維"],
                "evening": ["張晉顥"]
            },
            "FRI": {
                "morning": ["劉大維"],
                "afternoon": ["劉大維"],
                "evening": ["劉大維"]
            },
            "SAT": {
                "morning": ["劉大維"],
                "afternoon": ["輪診"],  # 特別標示
                "evening": None  # 休診
            },
            "SUN": {
                "morning": None,
                "afternoon": None,
                "evening": None
            }
        }
    },
    "banqiao_weili": {
        "clinic_id": "板橋維力",
        "name": "板橋維力骨科診所",
        "color": "#10b981",  # 綠色
        "source_url": "https://www.weili-clinic.com/news/category-5/post-30",
        "whitelist": ["高逢駿", "陳書佑"],  # 重點醫師
        "blacklist": [],
        "fixed_schedule": False,  # 需要定期更新
        "note": "板橋維力班表會調整，建議每週檢查網站確認",
        "last_updated": "2026-02-09",
        "valid_until": "2026-02-14",
        "schedule": {
            # 示例：2/9-2/14 週
            "MON": {
                "morning": ["高逢駿"],
                "afternoon": ["林茂森"],
                "evening": ["陳書佑"]
            },
            "TUE": {
                "morning": ["陳書佑"],
                "afternoon": ["陳書佑"],
                "evening": ["高逢駿"]
            },
            "WED": {
                "morning": ["陳奕成"],
                "afternoon": ["許芳維"],
                "evening": ["許芳維"]
            },
            "THU": {
                "morning": ["高逢駿"],
                "afternoon": ["陳書佑"],
                "evening": ["陳書佑"]
            },
            "FRI": {
                "morning": ["陳書佑"],
                "afternoon": ["高逢駿"],
                "evening": ["高逢駿"]
            },
            "SAT": {
                "morning": ["高逢駿"],
                "afternoon": ["陳書佑"],
                "evening": None  # 週六晚上休診
            },
            "SUN": {
                "morning": None,
                "afternoon": None,
                "evening": None
            }
        }
    }
}

def convert_to_schedules_format(date_range_start, date_range_end):
    """
  轉換為 schedules.json 格式
    需要：
    1. 將每日班表轉換為個別 session 物件
    2. 加入實際日期
    3. 符合現有 JSON schema
    """
    pass  # TODO: 實作轉換邏輯

if __name__ == "__main__":
    import json
    print(json.dumps(weili_clinics_data, ensure_ascii=False, indent=2))
