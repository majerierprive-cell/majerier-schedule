import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List
from auth.login import login
from services.rental_service import navigate_to_daily_schedule, download_excel_for_date
from services.rental_parser import parse_excel
from utils.file_utils import clean_dirs
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rentals", tags=["rentals"])


@router.get("")
async def get_rentals(
    dates: List[str] = Query(
        ..., description="조회할 날짜 리스트 (예: ?dates=2025-12-10&dates=2025-12-15)")
):
    driver = None
    try:
        clean_dirs()

        # FastAPI 기본 스펙: &dates=... 사용
        target_dates = []
        for d in dates:
            # 콤마로 들어오는 경우 방어 코드 (혹시나 해서)
            for split_d in d.split(','):
                try:
                    target_dates.append(datetime.strptime(
                        split_d.strip(), "%Y-%m-%d"))
                except:
                    pass

        target_dates = sorted(list(set(target_dates)))
        logger.info(f"수집 대상: {[d.strftime('%Y-%m-%d') for d in target_dates]}")

        from main import get_chrome_driver
        driver = get_chrome_driver()
        login(driver)
        navigate_to_daily_schedule(driver)

        all_data = []
        for curr in target_dates:
            d_str = curr.strftime("%Y-%m-%d")
            f = download_excel_for_date(driver, curr)
            if f:
                data = parse_excel(f, d_str)
                all_data.extend(data)
                # os.remove(f) # 디버깅용 (삭제 안함)
            else:
                logger.warning(f"{d_str}: 데이터 없음")

        return JSONResponse(content={
            "success": True,
            "total_count": len(all_data),
            "data": all_data
        })

    except Exception as e:
        logger.error(f"API 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            driver.quit()
