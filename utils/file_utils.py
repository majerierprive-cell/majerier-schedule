import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 디렉토리 경로 설정
BASE_DIR = os.getcwd()
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

# 디렉토리 생성
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def save_screenshot(driver, name: str):
    """스크린샷을 저장하는 함수"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(SCREENSHOT_DIR, f"{name}_{timestamp}.png")
        driver.save_screenshot(filepath)
        return filepath
    except Exception:
        return None


def clean_dirs():
    # (폴더경로, 삭제할 확장자 튜플) 리스트
    targets = [
        (DOWNLOAD_DIR, ('.xls', '.xlsx')),
        (SCREENSHOT_DIR, ('.png', '.html'))
    ]

    for folder, extensions in targets:
        if not os.path.exists(folder):
            continue

        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) and filename.lower().endswith(extensions):
                    os.unlink(file_path)
            except Exception:
                pass
