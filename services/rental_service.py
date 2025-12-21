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


def navigate_to_daily_schedule(driver):
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
                (By.XPATH, "//div[contains(text(), '대여일정')]")))
            logging.info("Find menu from name: %s", menu.text)
            driver.execute_script("arguments[0].click();", menu)
        except:
            menu = driver.find_element(By.XPATH, "/html/body/div/div/div[3]")
            logging.info("Find menu from element: %s", menu.text)
            driver.execute_script("arguments[0].click();", menu)

        time.sleep(2)
        driver.switch_to.default_content()
        try:
            driver.switch_to.frame(1)
        except:
            for f in driver.find_elements(By.TAG_NAME, "frame"):
                if f.get_attribute("name") != "topFrame":
                    driver.switch_to.frame(f)
                    break

        daily_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
            (By.XPATH, "//a[contains(text(), '일간')] | //a[contains(@href, 'rent_day')]")))
        driver.execute_script("arguments[0].click();", daily_btn)
        time.sleep(2)
    except Exception as e:
        save_screenshot(driver, "error_nav")
        raise e


def navigate_to_date(driver, target_date: datetime):
    try:
        driver.switch_to.default_content()
        try:
            driver.switch_to.frame(1)
        except:
            driver.switch_to.frame("mainFrame")

        t_str = target_date.strftime("%Y-%m-%d")
        t_day = str(target_date.day)

        for _ in range(24):
            try:
                selects = driver.find_elements(
                    By.CSS_SELECTOR, "#sidebar select")
                if len(selects) >= 2:
                    c_yr = int(
                        Select(selects[0]).first_selected_option.text.replace('년', '').strip())
                    c_mo = int(
                        Select(selects[1]).first_selected_option.text.replace('월', '').strip())
                else:
                    h_txt = driver.find_element(
                        By.CSS_SELECTOR, "#sidebar .lnb-cal tr:first-child").text
                    c_yr = int(re.search(r'(\d{4})', h_txt).group(1))
                    c_mo = int(re.search(r'(\d{1,2})', h_txt).group(1))

                if c_yr == target_date.year and c_mo == target_date.month:
                    break

                if (c_yr * 12 + c_mo) < (target_date.year * 12 + target_date.month):
                    btn = driver.find_element(
                        By.CSS_SELECTOR, "#sidebar .next, #sidebar a:contains('>')")
                else:
                    btn = driver.find_element(
                        By.CSS_SELECTOR, "#sidebar .prev, #sidebar a:contains('<')")
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
            except:
                break

        try:
            xpath = f"//div[contains(@class,'lnb-cal')]//td[not(contains(@class,'other'))]//a[normalize-space(text())='{t_day}']"
            date_link = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].click();", date_link)
        except:
            driver.execute_script(
                f"goPlanToday('{t_str}', '{target_date.year}', '{target_date.month}');")

        time.sleep(1)
        return True
    except Exception as e:
        save_screenshot(driver, f"err_date_{t_str}")
        raise e


def download_excel_for_date(driver, target_date: datetime):
    from utils.file_utils import DOWNLOAD_DIR
    date_str = target_date.strftime("%Y-%m-%d")
    try:
        navigate_to_date(driver, target_date)
        time.sleep(2)
        driver.switch_to.default_content()
        try:
            driver.switch_to.frame(1)
        except:
            driver.switch_to.frame("mainFrame")

        existing_files = set(os.listdir(DOWNLOAD_DIR))

        try:
            excel_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(text(), '엑셀')] | //a[contains(@href, 'excel')] | //img[contains(@src, 'excel')]/parent::a")))
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
