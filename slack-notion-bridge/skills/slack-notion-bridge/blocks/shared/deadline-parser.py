"""
자연어 기한 파싱 — "내일", "이번주 금요일", "4/20" 같은 표현을 YYYY-MM-DD로.

사용 시점: 자유 텍스트 메시지나 스레드 댓글에서 날짜를 뽑아
          Notion date 속성에 자동 입력하고 싶을 때.

지원 형식:
  - 절대: 2026-04-20, 2026/04/20, 2026.04.20, 4/20, 4.20, 4월 20일
  - 상대: 오늘, 내일, 모레, 글피, N일 후/뒤, N주 후/뒤, 일주일 후, 한달 후
  - 요일: 이번주 금요일, 다음주 월요일, 담주 수요일, 금요일, 금요일까지
  - 월말/월초: 이번달 말, 다음달 말, 이번달 초, 다음달 초

파싱 불가 시 None.

CUSTOMIZE:
  - 년도 모호성: 올해의 (월, 일)이 오늘보다 과거면 내년으로 가정. 필요 없으면 수정.
  - 요일 단독 매칭: 가장 가까운 미래 요일. 오늘 요일이면 다음주로.
"""

import calendar
import re
from datetime import datetime, timedelta

_WEEKDAY_KR = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}


def _end_of_month(d: datetime) -> datetime:
    last = calendar.monthrange(d.year, d.month)[1]
    return d.replace(day=last)


def _add_months(d: datetime, n: int) -> datetime:
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    return d.replace(year=year, month=month, day=1)


def parse_deadline(text: str, today: datetime | None = None) -> str | None:
    """텍스트에서 요청 기한을 추출하여 'YYYY-MM-DD' 형식으로 반환. 파싱 불가 시 None."""
    if not text:
        return None
    today = today or datetime.now()

    # 1) YYYY-MM-DD / YYYY/MM/DD / YYYY.MM.DD
    m = re.search(r"(\d{4})[-/.]\s*(\d{1,2})[-/.]\s*(\d{1,2})", text)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 2) M월 D일
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        try:
            year = today.year if (month, day) >= (today.month, today.day) else today.year + 1
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 3) 오늘/내일/모레/글피 — 긴 키워드부터
    simple_pairs = [
        ("내일모레", 2), ("모레", 2), ("글피", 3),
        ("오늘", 0), ("내일", 1), ("낼", 1),
    ]
    for kw, delta in simple_pairs:
        if kw in text:
            return (today + timedelta(days=delta)).strftime("%Y-%m-%d")

    # 4) N일 후, N주 후, 일주일 후, 한달 후
    m = re.search(r"(\d+)\s*일\s*(후|뒤)", text)
    if m:
        return (today + timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d")

    m = re.search(r"(\d+)\s*주\s*(후|뒤)", text)
    if m:
        return (today + timedelta(weeks=int(m.group(1)))).strftime("%Y-%m-%d")

    if re.search(r"일\s*주일\s*(후|뒤)", text):
        return (today + timedelta(days=7)).strftime("%Y-%m-%d")
    if re.search(r"(한\s*달|1\s*달|한달)\s*(후|뒤)", text):
        return _add_months(today, 1).strftime("%Y-%m-%d")

    # 5) 이번달/다음달 말/초
    if re.search(r"이번\s*달\s*말", text):
        return _end_of_month(today).strftime("%Y-%m-%d")
    if re.search(r"다음\s*달\s*말|담\s*달\s*말", text):
        return _end_of_month(_add_months(today, 1)).strftime("%Y-%m-%d")
    if re.search(r"이번\s*달\s*초", text):
        return today.replace(day=1).strftime("%Y-%m-%d")
    if re.search(r"다음\s*달\s*초|담\s*달\s*초", text):
        return _add_months(today, 1).strftime("%Y-%m-%d")

    # 6-1) 이번주 X요일
    m = re.search(r"이번\s*주\s*([월화수목금토일])\s*요일?", text)
    if m:
        target = _WEEKDAY_KR[m.group(1)]
        delta = target - today.weekday()
        if delta < 0:
            delta += 7
        return (today + timedelta(days=delta)).strftime("%Y-%m-%d")

    # 6-2) 다음주/담주 X요일
    m = re.search(r"(다음\s*주|담\s*주|담주)\s*([월화수목금토일])\s*요일?", text)
    if m:
        target = _WEEKDAY_KR[m.group(2)]
        this_monday = today - timedelta(days=today.weekday())
        next_monday = this_monday + timedelta(days=7)
        return (next_monday + timedelta(days=target)).strftime("%Y-%m-%d")

    # 6-3) 단독 요일 (가장 가까운 미래)
    m = re.search(r"([월화수목금토일])\s*요일", text)
    if m:
        target = _WEEKDAY_KR[m.group(1)]
        delta = target - today.weekday()
        if delta <= 0:
            delta += 7
        return (today + timedelta(days=delta)).strftime("%Y-%m-%d")

    # 7) M/D, M.D, M-D (연도 없음) — 숫자 오탐 방지 위해 맨 뒤
    m = re.search(r"(?<!\d)(\d{1,2})\s*[/.\-]\s*(\d{1,2})(?!\d)", text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            try:
                year = today.year if (month, day) >= (today.month, today.day) else today.year + 1
                return datetime(year, month, day).strftime("%Y-%m-%d")
            except ValueError:
                pass

    return None
