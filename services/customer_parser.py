import re
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def clean_text_list(text_list):
    """
    [문자열 세탁기]
    리스트를 합친 뒤, 지저분한 콤마(,,,)와 공백을 깔끔하게 정리합니다.
    """
    # 1. 빈 값 제거
    valid_texts = [t.strip()
                   for t in text_list if t.strip() and t.strip() != ',']

    # 2. 합치기 (일단 콤마로 연결)
    full_text = ", ".join(valid_texts)

    # 3. 정규식으로 청소
    # ", ," 또는 ",," 처럼 콤마가 반복되는 것을 하나로 통일
    full_text = re.sub(r'\s*,\s*', ', ', full_text)  # 공백 정리
    full_text = re.sub(r'(,\s*){2,}', ', ', full_text)  # 중복 콤마 제거

    # 4. 앞뒤 콤마 제거
    return full_text.strip(', ').strip()


def parse_customer_html_xls(path, date):
    logger.info(f"▶ HTML(Fake Excel) 파서 실행: {path}")
    res = []

    # 1. 인코딩 감지 (제공해주신 파일이 euc-kr이므로 이것부터 시도)
    encodings = ['euc-kr', 'cp949', 'utf-8']
    content = ""

    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc, errors='ignore') as f:
                temp = f.read()
                # 헤더 키워드로 올바른 인코딩인지 검증
                if '고객' in temp or '지점' in temp or '대여' in temp:
                    content = temp
                    logger.info(f"✔ 인코딩 확정: {enc}")
                    break
        except:
            continue

    if not content:
        logger.error("❌ 파일 내용을 읽을 수 없습니다.")
        return []

    try:
        soup = BeautifulSoup(content, 'html.parser')
        table = soup.find('table')
        if not table:
            return []

        rows = table.find_all('tr')
        headers = []
        start_row = 0

        # 2. 헤더 찾기
        for idx, row in enumerate(rows[:10]):
            cells = [c.get_text(strip=True).replace('\xa0', '')
                     for c in row.find_all(['td', 'th'])]
            if any(h in cells for h in ['지점', '고객명']):
                headers = cells
                start_row = idx + 1
                logger.info(f"✅ 헤더 발견: {headers}")
                break

        if not headers and rows:
            headers = [c.get_text(strip=True).replace('\xa0', '')
                       for c in rows[0].find_all(['td', 'th'])]
            start_row = 1

        # 3. 데이터 파싱
        for row in rows[start_row:]:
            cells = row.find_all(['td', 'th'])
            row_data = {}

            for c_idx, c in enumerate(cells):
                if c_idx >= len(headers):
                    break
                h = headers[c_idx]
                if not h:
                    h = f"Col_{c_idx}"

                # 컬럼 파싱
                raw_texts = [t.strip() for t in c.stripped_strings]
                row_data[h] = clean_text_list(raw_texts)

            # 유효 데이터 필터링
            cust = row_data.get('고객명', '').strip()
            if cust and cust != 'None':
                row_data['발주일'] = date
                res.append(row_data)

        logger.info(f"✔ 파싱 완료: {len(res)}건")
        return res

    except Exception as e:
        logger.error(f"HTML 파싱 오류: {e}")
        return []


def parse_customer_excel(path, date):
    try:
        # Fake Excel Check
        with open(path, 'rb') as f:
            if b'<!DOCTYPE' in f.read(20) or b'<html' in f.read(20):
                return parse_customer_html_xls(path, date)

        # 실제 XLS/XLSX는 기존 로직 유지 (생략)
        # 하지만 보통 Fake Excel이므로 여기로 넘어오는 경우는 드뭄
        return parse_customer_html_xls(path, date)  # 일단 HTML 파서로 보냄 (안전장치)

    except Exception:
        return parse_customer_html_xls(path, date)
