import os
import sys
import time
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


def login(driver):
    from main import LOGIN_URL, USERNAME, PASSWORD
    from utils.file_utils import save_screenshot
    logger.info("LOGIN_URL: %s", LOGIN_URL)
    logger.info("name: %s", USERNAME)
    logger.info("pw: %s", PASSWORD)
    try:
        driver.get(LOGIN_URL)
        time.sleep(1)
        driver.find_element(By.ID, "Login_id").send_keys(USERNAME)
        driver.find_element(By.ID, "Login_pw").send_keys(PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        time.sleep(2)
        if "login" in driver.current_url.lower():
            raise Exception("로그인 실패")
        logger.info("로그인 성공")
        return True
    except Exception as e:
        save_screenshot(driver, "error_login")
        raise e
