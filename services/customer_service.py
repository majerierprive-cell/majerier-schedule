import os
import time
import re
import logging
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from utils.file_utils import save_screenshot

logger = logging.getLogger(__name__)


def navigate_to_customer_daily_schedule(driver):
    try:
        logger.info("메뉴 이동 중...")
        driver.switch_to.default_content()
        time.sleep(0.5)
        try:
            driver.switch_to.frame("topFrame")
        except:
            driver.switch_to.frame(0)

        try:
            menu = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(text(), '고객관리')]")))
            logging.info("Find menu from name: %s", menu.text)
            driver.execute_script("arguments[0].click();", menu)
        except:
            menu = driver.find_element(By.XPATH, "/html/body/div/div/div[1]")
            logging.info("Find menu from element: %s", menu.text)
            driver.execute_script("arguments[0].click();", menu)

        time.sleep(2)
    except Exception as e:
        save_screenshot(driver, "error_nav")
        raise e


def navigate_to_customer_date(driver, target_date: datetime):
    try:
        driver.switch_to.default_content()
        try:
            driver.switch_to.frame(1)
        except:
            driver.switch_to.frame("mainFrame")

        t_str = target_date.strftime("%Y-%m-%d")
        # 계약 고객 클릭
        try:
            logger.info("계약고객 메뉴 클릭 시도")
            # 1. 텍스트로 찾기
            try:
                link = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(), '계약고객')]")))
                driver.execute_script("arguments[0].click();", link)
            except:
                # 2. href로 찾기
                link = driver.find_element(
                    By.XPATH, "//a[contains(@href, 'member_list.php')]")
                driver.execute_script("arguments[0].click();", link)
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"계약고객 메뉴 이동 실패: {e}")
            raise e

        # 조회기간 날짜 지정 st, end 둘 다 target date 로 지정
        try:
            logger.info(f"날짜 설정: {t_str}")
            # sDay, eDay ID를 사용하여 날짜 설정
            script = f"""
                document.getElementById('sDay').value = '{t_str}';
                document.getElementById('eDay').value = '{t_str}';
            """
            driver.execute_script(script)
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"날짜 설정 실패: {e}")
            raise e

        # 검색 클릭
        try:
            logger.info("검색 버튼 클릭")
            search_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@type='submit' and contains(text(), '검색')]")))
            driver.execute_script("arguments[0].click();", search_btn)
            time.sleep(2)
        except Exception as e:
            logger.error(f"검색 버튼 클릭 실패: {e}")
            pass


    except Exception as e:
        save_screenshot(driver, f"err_date_{t_str}")
        raise e


def download_excel_for_customer_date(driver, target_date: datetime):
    from utils.file_utils import DOWNLOAD_DIR
    date_str = target_date.strftime("%Y-%m-%d")
    try:
        navigate_to_customer_date(driver, target_date)
        time.sleep(2)
        driver.switch_to.default_content()
        try:
            driver.switch_to.frame(1)
        except:
            driver.switch_to.frame("mainFrame")

        existing_files = set(os.listdir(DOWNLOAD_DIR))

        # 엑셀 조회 버튼 클릭
        try:
            excel_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                (By.XPATH, "//img[contains(@src, 'excel')]")))
            driver.execute_script("arguments[0].click();", excel_btn)
        except Exception as e:
            logger.error(f"엑셀 버튼 못찾음: {e}")
            return None

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            driver.switch_to.alert.accept()
            return None
        except:
            pass

        for i in range(15):
            current_files = set(os.listdir(DOWNLOAD_DIR))
            new_files = current_files - existing_files
            valid_files = [f for f in new_files if f.endswith(
                '.xls') or f.endswith('.xlsx')]
            if valid_files:
                f_path = os.path.join(DOWNLOAD_DIR, valid_files[0])
                time.sleep(1)
                return f_path
            time.sleep(1)
        return None
    except Exception:
        return None
