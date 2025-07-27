from typing import Literal

# 금융 기관
Institution = Literal["KB국민은행", "신한은행", "하나은행", "우리은행", "NH농협은행", "IBK기업은행", "KDB산업은행",
                      "전북은행", "케이뱅크", "경남은행", "부산은행", "카카오뱅크", "광주은행", "SH수협은행", "iM뱅크",
                      "제주은행", "토스뱅크", "SC제일은행"]

# 기간 단위 (연, 월, 일)
TermUnit = Literal["month", "day", "year"]


def unit_map(unit: TermUnit):
    match unit:
        case "day":
            return "일"
        case "month":
            return "개월"
        case "year":
            return "년"
