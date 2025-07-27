from typing import Literal

# 금리 유형
# - fixed: 고정금리
# - variable: 변동금리
SavingInterestType = Literal["fixed", "variable"]

# 적립 방식
# - fixed: 정액적립식
# - flexible: 자유적립식
SavingEarnMethod = Literal["fixed", "flexible"]

# 우대금리 유형
# - user_choice: 가입기간 중 개인의 선택이나 노력으로 수혜 가능한 항목
# - pre_condition: 가입기간 전 개인의 상태에 따라 수혜여부가 결정되는 항목
# - event_based: 개인의 선택이나 상태와 무관한 이벤트성/무작위성 항목
SavingPreferentialRateType = Literal["user_choice", "pre_condition", "event_based"]
