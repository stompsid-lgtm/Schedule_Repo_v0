#!/usr/bin/env python3
"""
維力骨科診所門診表爬蟲
抓取網頁並截圖門診表，使用 OCR 提取醫師姓名與排班資訊
"""

import time
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from PIL import Image
import json

# 設定
URL = "https://www.weili-clinic.com/news/category-5/post-30"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

def setup_driver():
    """設定瀏覽器"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 無頭模式
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=options)
    return driver

def capture_schedule_images(driver):
    """截圖門診表"""
    driver.get(URL)
    time.sleep(3)  # 等待頁面載入
    
    # 關閉可能的彈窗
    try:
        close_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='close']"))
        )
        close_btn.click()
        time.sleep(1)
    except:
        pass
    
    # 滾動到門診表位置
    driver.execute_script("window.scrollBy(0, 1000);")
    time.sleep(2)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 截圖板橋門診表（示意位置）
    banqiao_img = OUTPUT_DIR / f"banqiao_schedule_{timestamp}.png"
    driver.save_screenshot(str(banqiao_img))
    
    # 繼續滾動到土城門診表
    driver.execute_script("window.scrollBy(0, 800);")
    time.sleep(2)
    
    tucheng_img = OUTPUT_DIR / f"tucheng_schedule_{timestamp}.png"
    driver.save_screenshot(str(tucheng_img))
    
    return {
        "banqiao": str(banqiao_img),
        "tucheng": str(tucheng_img)
    }

def extract_schedule_from_images(image_paths):
    """
    使用 OCR 從圖片提取門診表資料
    目前先返回示例資料結構，實際 OCR 需要整合 pytesseract 或 Google Vision API
    """
    
    # TODO: 實作 OCR 提取邏輯
    # 這裡先返回固定格式，供後續開發參考
    
    schedule_data = {
        "banqiao": {
            "clinic_id": "板橋維力",
            "doctors": ["高逢駿", "陳書佑", "陳奕成", "林茂森", "許芳維"],
            "schedule": {
                "MON": {
                    "morning": ["高逢駿"],
                    "afternoon": ["林茂森"],
                    "evening": ["陳書佑"]
                },
                # ... 其他日期
            }
        },
        "tucheng": {
            "clinic_id": "土城維力",
            "doctors": ["劉大維", "張晉顥", "楊欣諭"],
            "schedule": {
                "MON": {
                    "morning": ["劉大維"],
                    "afternoon": ["劉大維"],
                    "evening": ["張晉顥"]
                },
                # ... 其他日期
            }
        }
    }
    
    return schedule_data

def save_to_json(data, output_file):
    """儲存為 JSON 格式"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已儲存至 {output_file}")

def main():
    """主程式"""
    print("🚀 開始抓取維力骨科門診表...")
    
    driver = setup_driver()
    
    try:
        # 1. 截圖門診表
        print("📸 截圖門診表...")
        image_paths = capture_schedule_images(driver)
        print(f"   板橋: {image_paths['banqiao']}")
        print(f"   土城: {image_paths['tucheng']}")
        
        # 2. 提取資料
        print("\n🔍 提取門診資料...")
        schedule_data = extract_schedule_from_images(image_paths)
        
        # 3. 儲存結果
        output_file = OUTPUT_DIR / f"weili_schedule_{datetime.now().strftime('%Y%m%d')}.json"
        save_to_json(schedule_data, output_file)
        
        print("\n✨ 完成!")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
