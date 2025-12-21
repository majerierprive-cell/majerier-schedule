import re
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup, NavigableString, Tag

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


def extract_red_text_html(td_tag):
    """
    HTML 태그 내 텍스트 색상 판별 (CSS 상속 우선순위 적용)
    """
    normal_parts = []
    red_parts = []

    # <br> 태그는 콤마로 치환 (줄바꿈 = 상품 구분)
    for br in td_tag.find_all("br"):
        br.replace_with(",")

    # 모든 하위 텍스트 노드를 순회
    for element in td_tag.descendants:
        # 텍스트 노드인 경우만 처리
        if isinstance(element, NavigableString):
            text = element.strip()
            # 의미 없는 기호 무시
            if not text or text == ",":
                continue

            # [핵심 로직] 부모를 거슬러 올라가며 "가장 가까운 색상" 찾기
            is_red = False      # 기본값
            color_found = False  # 색상 정의를 찾았는지 여부

            parent = element.parent
            while parent:
                # 더 이상 검사할 태그가 없거나 테이블 셀을 벗어나면 중단
                if not isinstance(parent, Tag) or parent.name == '[document]':
                    break

                attrs = parent.attrs
                style = attrs.get('style', '').lower().replace(" ", "")
                color = attrs.get('color', '').lower()

                # 1. 빨간색 정의 확인
                is_explicit_red = ('color:red' in style) or \
                                  ('color:#ff' in style and len(style.split('color:#ff')[1].split(';')[0]) <= 4) or \
                                  (color == 'red') or (color.startswith('#ff'))

                # 2. 빨간색이 아닌 다른 색상 정의 확인 (blue, black 등)
                # color: 속성이 있는데 red가 아니면 다른 색임
                is_explicit_other = ('color:' in style and not is_explicit_red) or \
                                    (color and not is_explicit_red)

                if is_explicit_other:
                    # 다른 색(파란색 등)이 먼저 감지됨 -> 일반 상품
                    is_red = False
                    color_found = True
                    break

                if is_explicit_red:
                    # 빨간색이 먼저 감지됨 -> 추가 상품
                    is_red = True
                    color_found = True
                    break

                # td 태그까지 왔는데 별다른 색상 정의가 없었다면?
                # (td 자체의 색상을 확인하고 루프 종료)
                if parent.name == 'td':
                    break

                parent = parent.parent

            # 찾은 결과에 따라 분류
            if is_red:
                red_parts.append(text)
            else:
                normal_parts.append(text)

    return clean_text_list(normal_parts), clean_text_list(red_parts)


def parse_html_xls(path, date):
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

                # [수정됨] 대여상품 컬럼 파싱
                if '대여' in h and '상품' in h:  # '대여상품', '대여 상품' 등 유연하게
                    normal_txt, red_txt = extract_red_text_html(c)
                    row_data['대여상품'] = normal_txt
                    row_data['추가상품'] = red_txt
                else:
                    # 일반 컬럼도 텍스트 클리닝 적용
                    raw_texts = [t.strip() for t in c.stripped_strings]
                    row_data[h] = clean_text_list(raw_texts)

            # 유효 데이터 필터링
            cust = row_data.get('고객명', '').strip()
            # 고객명에 '담당자' 같은 헤더성 데이터가 섞여 들어오면 제외
            if cust and cust != 'None' and '담당자' not in cust:
                row_data['대여일자'] = date
                res.append(row_data)

        logger.info(f"✔ 파싱 완료: {len(res)}건")
        return res

    except Exception as e:
        logger.error(f"HTML 파싱 오류: {e}")
        return []


def parse_excel(path, date):
    try:
        # Fake Excel Check
        with open(path, 'rb') as f:
            if b'<!DOCTYPE' in f.read(20) or b'<html' in f.read(20):
                return parse_html_xls(path, date)

        # 실제 XLS/XLSX는 기존 로직 유지 (생략)
        # 하지만 보통 Fake Excel이므로 여기로 넘어오는 경우는 드뭄
        return parse_html_xls(path, date)  # 일단 HTML 파서로 보냄 (안전장치)

    except Exception:
        return parse_html_xls(path, date)
