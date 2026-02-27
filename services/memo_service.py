import os
import sys
import time
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.file_utils import save_screenshot

logger = logging.getLogger(__name__)

def register_memo(driver, schedule_type: str, target_date: datetime, customer_name: str, memo_type: int):
    """
    고객명과 메모 유형을 입력받아 각 일정표에서 고객을 찾아 메모를 등록하는 통합 API.
    
    :param driver: selenium webdriver
    :param schedule_type: 'rental' (대여일정), 'shop' (샵일정), 'customer' (계약고객) 중 하나
    :param target_date: 검색할 날짜 (datetime 객체)
    :param customer_name: 고객명 (예: "홍길동1234" 등 이름+전화번호뒷자리)
    :param memo_type: 메모 유형 (1~8)
    """
    logger.info(f"메모 등록 시작: 타입={schedule_type}, 날짜={target_date.strftime('%Y-%m-%d')}, 고객명={customer_name}, 메모={memo_type}")
    
    # 1. 메뉴 및 날짜 이동
    # 각각의 메뉴 날짜 이동 함수를 import 하여 재사용합니다.
    try:
        if schedule_type == 'rental':
            from services.rental_service import navigate_to_daily_schedule, navigate_to_date
            navigate_to_daily_schedule(driver)
            navigate_to_date(driver, target_date)
            
        elif schedule_type == 'shop':
            from services.shop_service import navigate_to_shop_daily_schedule, navigate_to_shop_date
            navigate_to_shop_daily_schedule(driver)
            navigate_to_shop_date(driver, target_date)
            
        elif schedule_type == 'customer':
            from services.customer_service import navigate_to_customer_daily_schedule, navigate_to_customer_date
            navigate_to_customer_daily_schedule(driver)
            navigate_to_customer_date(driver, target_date)
            
        else:
            raise ValueError("유효하지 않은 schedule_type 입니다. ('rental', 'shop', 'customer' 중 선택)")
    except Exception as e:
        logger.error(f"날짜 이동 중 오류 발생: {e}")
        raise e

    time.sleep(2)  # 페이지 로딩 대기

    # 프레임 전환 (mainFrame 또는 1번 프레임)
    driver.switch_to.default_content()
    try:
        driver.switch_to.frame(1)
    except:
        try:
            driver.switch_to.frame("mainFrame")
        except:
            pass
            
    # 2. 고객명 <a> 태그 찾아서 클릭
    try:
        # 고객명이 포함된 <a> 태그 찾기 (공백 등 오차 방지를 위해 normalize-space 사용 가능)
        xpath = f"//a[contains(text(), '{customer_name}')] | //a[contains(normalize-space(text()), '{customer_name}')]"
        customer_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].click();", customer_link)
    except Exception as e:
        logger.error(f"고객 '{customer_name}'을(를) 찾을 수 없거나 클릭할 수 없습니다: {e}")
        save_screenshot(driver, f"err_memo_find_{customer_name}")
        raise e

    time.sleep(2)  # 팝업 열리는 시간 대기
    
    # 3. 팝업 창 핸들링 
    main_window = driver.current_window_handle
    all_windows = driver.window_handles
    
    popup_window = None
    for window in all_windows:
        if window != main_window:
            popup_window = window
            break
            
    if not popup_window:
        logger.error("팝업 창이 열리지 않았습니다.")
        raise Exception("팝업 창이 열리지 않았습니다.")
        
    driver.switch_to.window(popup_window)
    
    try:
        time.sleep(1) # 팝업 로딩 대기
        
        # 팝업 내부에 iframe이 있을 수 있으므로 프레임 전환 시도
        try:
            # 캡처 화면에 따라 실제 select 요소가 존재하는 consultFrame으로 전환
            consult_frame = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "consultFrame"))
            )
            driver.switch_to.frame(consult_frame)
        except Exception as e:
            logger.warning(f"consultFrame 전환 실패: {e}")
            pass

        # 4. 메모(알림톡) 코드 선택 대상 매핑
        memo_code_map = {
            1: "237",   # [알림톡1]예약확정안내
            2: "240",   # [알림톡2]리뷰/계약자
            3: "239",   # [알림톡3]스마트 가봉
            4: "238",   # [알림톡4]보증금 안내
            5: "9131",  # [알림톡5]픽업/반납안내
            6: "9134",  # [알림톡6]출고당일안내
            7: "9132",  # [알림톡7]드레스반납안내
            8: "9135"   # [알림톡8]체크아웃
        }
        
        code_value = memo_code_map.get(int(memo_type))
        if not code_value:
            raise ValueError(f"유효하지 않은 메모 유형입니다: {memo_type}. (1~8 사이의 숫자여야 합니다.)")
            
        # 선택박스(select name="code") 찾아서 선택
        code_select_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.NAME, "code"))
        )
        
        # 스크롤 최하단으로 이동시켜 요소가 보이게 함
        driver.execute_script("arguments[0].scrollIntoView(true);", code_select_element)
        time.sleep(0.5)

        select = Select(code_select_element)
        select.select_by_value(code_value)
        
        time.sleep(0.5)
        
        # 5. 등록 이미지 버튼 클릭 (<img id="btnReg" ... />)
        register_btn = driver.find_element(By.ID, "btnReg")
        driver.execute_script("arguments[0].click();", register_btn)
        
        # 알럿(완료 메시지 등)이 뜨면 수락 처리
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            logger.info(f"메모 등록 완료. 알럿 메시지: {alert.text}")
            alert.accept()
        except:
            pass
            
    except Exception as e:
        logger.error(f"팝업 내 메모 코드 선택 및 등록 중 오류 발생: {e}")
        save_screenshot(driver, f"err_memo_popup_{customer_name}")
        raise e
    finally:
        # 6. 팝업 창 닫기 및 메인 창 복귀
        try:
            driver.close()
        except:
            pass
        driver.switch_to.window(main_window)
        # 프레임 다시 전환
        driver.switch_to.default_content()
        try:
            driver.switch_to.frame(1)
        except:
            try:
                driver.switch_to.frame("mainFrame")
            except:
                pass
                
    logger.info("메모 등록 함수 실행 완료.")
    return True
