import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from datetime import datetime
from pydantic import BaseModel
from auth.login import login
from services.memo_service import register_memo
from utils.file_utils import clean_dirs
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memos", tags=["memos"])

class MemoRequest(BaseModel):
    schedule_type: str  # 'rental', 'shop', 'customer'
    target_date: str    # 'YYYY-MM-DD'
    customer_name: str  # e.g., '홍길동1234'
    memo_type: int      # 1~8

@router.post("")
async def create_memo(request: MemoRequest):
    driver = None
    try:
        try:
            target_date_obj = datetime.strptime(request.target_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            
        if request.schedule_type not in ['rental', 'shop', 'customer']:
            raise HTTPException(status_code=400, detail="Invalid schedule_type. Must be 'rental', 'shop', or 'customer'")
            
        if not (1 <= request.memo_type <= 8):
            raise HTTPException(status_code=400, detail="Invalid memo_type. Must be between 1 and 8")

        from main import get_chrome_driver
        driver = get_chrome_driver()
        login(driver)
        
        success = register_memo(
            driver=driver,
            schedule_type=request.schedule_type,
            target_date=target_date_obj,
            customer_name=request.customer_name,
            memo_type=request.memo_type
        )
        
        return JSONResponse(content={
            "success": success,
            "message": "메모 등록 성공" if success else "메모 등록 실패"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            driver.quit()
