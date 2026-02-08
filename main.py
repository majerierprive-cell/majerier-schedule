from fastapi import FastAPI
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from utils.file_utils import DOWNLOAD_DIR
# 로컬용
# from dotenv import load_dotenv
# load_dotenv(override=True)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경변수 설정
LOGIN_URL = os.environ.get("LOGIN_URL")
USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")


def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument(
        '--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
        "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver


app = FastAPI(title="Schedule API")

# 라우트 등록 (순환 import 방지를 위해 여기서 import)
from routes.rental import router as rental_router
from routes.shop import router as shop_router
from routes.customer import router as customer_router
app.include_router(rental_router)
app.include_router(shop_router)
app.include_router(customer_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
