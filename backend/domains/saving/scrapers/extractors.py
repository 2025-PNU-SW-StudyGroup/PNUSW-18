import json
from typing import List
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import TypeAdapter

from common.decorators.asyncio import retry_async
from domains.saving.models import BaseInterestRateTier, SavingPreferentialRate

import os
import asyncio

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")

saving_preferential_rate_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "saving_preferential_rate",
        "strict": True,
        "schema": {
            "type": "object",
            "description": "우대금리 조건 단일 객체",
            "properties": {
                "description": {
                    "type": "string"
                },
                "rate_type": {
                    "type": "string",
                    "enum": ["user_choice", "pre_condition", "event_based"]
                },
                "tiers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "condition": {
                                "type": "string"
                            },
                            "interest_rate": {
                                "type": "number",
                                "description": "연 금리(%p)"
                            }
                        },
                        "required": ["condition", "interest_rate"],
                        "additionalProperties": False,
                    }
                }
            },
            "additionalProperties": False,
            "required": ["description", "rate_type", "tiers"]
        },
    }
}

import re
from typing import List, Dict

# Compile primary interest patterns
PATTERNS = [
    re.compile(r'연\s*(\d+(?:\.\d+)?)\s*%p?'),  # "연 0.4%p" or "연 0.4%"
    re.compile(r'(\d+(?:\.\d+)?)\s*%p'),  # "0.4%p"
    re.compile(r'우대\w*\s*[이자율금리]*\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*%'),  # "우대이자율 : 2.2%"
    re.compile(r'[:]\s*(\d+(?:\.\d+)?)\s*%$'),  # " ... : 0.05%"
]

NEG_KW = {'정부기여금', '지급비율', '배율', '적립', '해지', 'X', '×'}


def is_negative(line: str):
    return any(kw in line for kw in NEG_KW)


def extract_interest(text: str) -> List[Dict]:
    results = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines:
        if is_negative(line):
            continue
        for pat in PATTERNS:
            m = pat.search(line)
            if m:
                val = float(m.group(1))
                # detect condition text
                if ':' in line:
                    cond = line.split(':')[0].strip(' -•')
                elif '연' in line:
                    cond = line.split('연')[0].strip(' -•')
                else:
                    cond = line[:80]
                results.append({"condition": cond, "interest_rate": val})
                break
    return results


PREFERENTIAL_INTEREST_RATE_AGENT_SYSTEM_PROMPT = """\
역할
  당신은 ‘적금 우대금리 데이터 태깅 엔진’이다. 입력된 안내문에서 **우대금리 조건**만 추출해 지정된 JSON 스키마로 반환한다.

출력
  • 반드시 saving_preferential_rate_response_format 스키마를 **100 %** 준수한 **단일 JSON**만 출력한다.  
  • JSON 이외의 텍스트·주석·코드 블록은 절대 포함하지 않는다.

추출 규칙
  1. **description** – 안내문의 제목·핵심 문구를 간결히 사용하며 불필요한 수식어는 제거한다.
  2. **rate_type** – 아래 기준으로 택일한다.  
     · 고객 행동·선택 달성형 → "user_choice"  
     · 계좌·거래 조건 등 자동 부여형 → "pre_condition"  
     · 이벤트·추첨·기간 한정 프로모션 → "event_based"
  3. **tiers** – 조건별 상세 금리 목록  
     · 안내문에 나타난 **정확한 숫자(소수 가능)**만 interest_rate 필드에 기록하며 단위(%p)는 제외한다. 예) 0.4  
     · ‘이상·초과·미만’ 등 범위형 문장은 condition 을 그대로 서술하고 interest_rate 에는 해당 문장에 등장하는 **가장 큰 단일 수치**를 사용한다.  
     · 동일 rate 값이라도 조건이 다르면 tiers 항목을 분리한다.  
     · 숫자가 명시되지 않은 조건은 tiers 에 포함하지 않는다.
  4. **안내문에 금리 숫자가 전혀 없으면 tiers=[] 로 반환**한다.
  5. 기본금리·정부지원금·세제 혜택 등 우대금리와 무관한 내용은 무시한다.
  6. 중복·동일 조건은 통합하고, 공백·개행·특수문자를 정리해 깔끔히 출력한다.
"""


@retry_async(times=20, delay=1)
async def extract_saving_preferential_rates(
        client: AsyncOpenAI,
        raw_text: str,
        model: str = "solar-pro2") -> SavingPreferentialRate:
    """
    우대금리 원문에서 SavingPreferentialRate 리스트를 추출한다.

    Args:
        client (AsyncOpenAI): OpenAI 비동기 클라이언트
        raw_text (str): 우대금리 설명이 포함된 원문
        model (str): 사용할 모델

    Returns:
        List[SavingPreferentialRate]: 파싱된 우대금리 정보
    """

    try:

        _client = AsyncOpenAI()
        response = await _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": PREFERENTIAL_INTEREST_RATE_AGENT_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": raw_text
                },
            ],
            response_format=saving_preferential_rate_response_format,  # type: ignore
            max_tokens=16384,
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("잘못된 응답입니다.")

        data = json.loads(content, strict=False)

    except Exception as e:
        print("우대금리 정보 추출 오류: ", raw_text)
        raise e

    return SavingPreferentialRate.model_validate(data)


base_rate_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "base_interest_rates",
        "strict": True,
        "schema": {
            "type": "array",
            "description": "가입 기간 구간별 기본 금리 목록",
            "items": {
                "type": "object",
                "properties": {
                    "min_term": {
                        "type": "integer",
                        "description": "구간 하단(포함), 단위: month"
                    },
                    "max_term": {
                        "type": "integer",
                        "description": "구간 상단(미포함). -1 → 상한 없음"
                    },
                    "interest_rate": {
                        "type": "number",
                        "description": "해당 구간의 연 금리(%p)"
                    }
                },
                "required": ["min_term", "interest_rate"]
            }
        }
    }
}

BASE_INTEREST_RATE_SYSTEM_PROMPT = ("당신은 금융 데이터 추출 어시스턴트입니다.\n"
                                    "주어진 표 데이터에 포함된 '기간별 만기 이율'에 대하여 "
                                    "가입 기간 범위와 연 금리를 추출해야 한다.\n\n"
                                    "다음 규칙을 반드시 따라야 한다.\n"
                                    "1. 기간이 'N개월 이상 M개월 미만' -> min_term=N, max_term=M\n"
                                    "2. 'N개월 이상' -> min_term=N, max_term=null\n"
                                    "3. 'N년만기' -> min_term=N*12, max_term=N*12\n"
                                    "4. 금리는 '%', 'p' 등 기호를 제거하고 float로 반환\n\n"
                                    "주어진 JSON Schema를 정확히 준수해라.")


@retry_async(times=20, delay=1)
async def extract_base_interest_rate_tiers(
    client: AsyncOpenAI,
    html_snippet: str,
    model: str = "solar-pro2",
) -> List[BaseInterestRateTier]:
    """
    HTML 테이블에서 기본 금리 구간을 추출한다.

    Args:
        client (AsyncOpenAI): OpenAI 비동기 클라이언트
        html_snippet (str): <table> 태그를 포함한 HTML 부분
        model (str): 사용할 모델명

    Returns:
        List[BaseInterestRateTier]: 구간별 기본 금리 정보
    """
    try:
        resp = await client.chat.completions.create(
            model=model,
            temperature=0.3,
            reasoning_effort="medium",
            messages=[
                {
                    "role": "system",
                    "content": BASE_INTEREST_RATE_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": html_snippet
                },
            ],
            response_format=base_rate_response_format,  # type: ignore
            max_tokens=16384,
        )

        content = resp.choices[0].message.content

        if not content:
            raise ValueError("잘못된 응답입니다.")

        data = json.loads(content, strict=False)

    except Exception as e:
        print("기본금리 추출 오류: ", html_snippet)
        raise e

    return TypeAdapter(List[BaseInterestRateTier]).validate_python(data)


if __name__ == "__main__":
    text1 = """\
    이벤트 우대이율 받는 방법
    ① 씨드받기 : 전월 적금 납입시 당월 씨드 1개 자동 생성(월 최대 1개 / 계약기간 내 최대 11개)
    ② 씨드확인 : 씨드 확인페이지(My씨드)에서 슈퍼씨드 당첨여부 확인- 경로 : JB뱅크(App) 로그인 → 전체메뉴 → 조회 → 전계좌조회 → JB슈퍼씨드 적금 [My씨드]-
     씨드 미확인 시 이벤트 우대금리(슈퍼씨드금리) 적용 불가- 이벤트 우대금리(슈퍼씨드금리) 중복 당첨 불가
     ③ 슈퍼씨드 금리적용 : 만기해지시 
    자동 적용 (중도해지시 적용불가)※ 슈퍼씨드 지급기준당월 생성되는 씨드 500개당 1개 지급 (매월 최소 1개 지급)→ 당월 슈퍼씨드 개수 = 당월 

    생성되는 전체 씨드 개수 X 0.2% & 소수점 이하 절상※ 슈퍼씨드 금리는 납입금액 전체에 적용 : 10%"""

    text2 = """\
    이벤트 우대이율 받는 방법
    ① 씨드받기 : 전월 적금 납입시 당월 씨드 1개 자동 생성(월 최대 1개 / 계약기간 내 최대 11개)
    ② 씨드확인 : 씨드 확인페이지(My씨드)에서 슈퍼씨드 당첨여부 확인
    - 경로 : JB뱅크(App) 로그인 → 전체메뉴 → 조회 → 전계좌조회 → JB슈퍼씨드 적금 [My씨드]
    - 씨드 미확인 시 이벤트 우대금리(슈퍼씨드금리) 적용 불가
    - 이벤트 우대금리(슈퍼씨드금리) 중복 당첨 불가
    ③ 슈퍼씨드 금리적용 : 만기해지시 자동 적용 (중도해지시 적용불가)
    ※ 슈퍼씨드 지급기준
    당월 생성되는 씨드 500개당 1개 지급 (매월 최소 1개 지급)
    → 당월 슈퍼씨드 개수 = 당월 생성되는 전체 씨드 개수 X 0.2% & 소수점 이하 절상
    ※ 슈퍼씨드 금리는 납입금액 전체에 적용 : 10%"""

    text = text1.rstrip()

    client = AsyncOpenAI()

    result = asyncio.run(extract_saving_preferential_rates(client=client,
                                                           raw_text=text))

    print(result)
