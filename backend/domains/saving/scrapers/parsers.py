from datetime import date
from typing import Dict

from openai import AsyncOpenAI, OpenAI

from common.decorators.asyncio import retry_async, retry_sync
from domains.common.types import TermUnit
from domains.saving.models import AmountPolicy, TermPolicy

import re

import json

import os
from dotenv import load_dotenv

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")


@retry_async(times=10, delay=1)
async def _parse_term_policy_llm(text: str, client: AsyncOpenAI) -> TermPolicy:

    try:

        schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "term_policy",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "policy_type": {
                            "type": "string",
                            "enum": [
                                "RANGE", "FIXED_DURATION", "CHOICES", "FIXED_DATE"
                            ],
                            "description": "기간 정책 유형"
                        },
                        "min_term": {
                            "type": "integer",
                            "description": "최소 가입 기간"
                        },
                        "max_term": {
                            "type": "integer",
                            "description": "최대 가입 기간"
                        },
                        "choices": {
                            "type": "array",
                            "items": {
                                "type": "integer",
                                "description": "선택 가능한 가입 기간"
                            },
                            "description": "가입 기간 선택지 목록"
                        },
                        "term_unit": {
                            "type": "string",
                            "enum": ["day", "month", "year"],
                            "description": "가입 기간 단위"
                        },
                        "maturity_date": {
                            "type": "string",
                            "format": "date",
                            "description": "만기일(고정형 상품)"
                        }
                    },
                    "required": ["policy_type"]
                }
            }
        }

        SYSTEM_PROMPT = """\
        당신의 역할은 입력받은 한국어 금융상품 설명 문장에서 "가입 기간 정책(TermPolicy)" 정보를 **JSON 객체**로만 추출하여 반환하는 것이다.  
        반환 결과는 아래 JSON Schema를 반드시 충족해야 하며, 추가·누락된 키가 존재해서는 안 된다.

        - JSON Schema
        {
          "policy_type": "RANGE | FIXED_DURATION | CHOICES | FIXED_DATE",   // 필수
          "min_term":     integer,   // RANGE, FIXED_DURATION
          "max_term":     integer,   // RANGE, FIXED_DURATION
          "choices":      integer[], // CHOICES
          "term_unit":    "day | month | year",   // RANGE, FIXED_DURATION, CHOICES
          "maturity_date":"YYYY-MM-DD"            // FIXED_DATE
        }

        - 조건 (policy_type에 따른 필수·금지 필드)
        1. **RANGE**  
           - 반드시 `min_term`, `max_term`, `term_unit`을 포함하고 `choices`, `maturity_date`는 넣지 않는다.
        2. **FIXED_DURATION**  
           - 하나의 고정 기간이라도 `min_term` · `max_term` · `term_unit`을 모두 채운다  
             (예: 12개월 상품 → min_term = max_term = 12, term_unit = "month").
        3. **CHOICES**  
           - `choices` 배열과 `term_unit`만 포함한다.  
           - `min_term`, `max_term`, `maturity_date`는 포함하지 않는다.
        4. **FIXED_DATE**  
           - 오직 `maturity_date`만 포함한다(예: "2026-01-11").  
           - 다른 기간 관련 필드는 넣지 않는다.

        - 공통 규칙
            - 모든 숫자는 정수로, 단위(개월·일·년)는 제외하고 적는다.
            - `term_unit` 값은 반드시 소문자로(day, month, year 중 하나).
            - ISO 8601 형식(YYYY-MM-DD) 외 날짜 표현은 사용하지 않는다.
        """

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": text
            },
        ]

        response = await client.chat.completions.create(
            model="solar-pro",
            messages=messages,  # type: ignore
            response_format=schema,  # type: ignore
            max_tokens=16384,
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("올바르지 않은 값입니다.")

        data = json.loads(content)
    except Exception as e:
        print(f"기간 정책 추출 중 오류 발생: ", text)
        raise e

    return TermPolicy(**data)


async def parse_term_policy(text: str, client: AsyncOpenAI) -> TermPolicy:
    """입력된 문자열에서 가입 기간 정책 파싱

    Args:
        text (str): 가입 기간 원본 텍스트 (ex: "1년", "90일 이상")

    Returns:
        TermPolicy: 파싱된 가입 기간 정책 인스턴스

    Raises:
        ValueError: 텍스트에서 유효한 정책을 찾지 못한 경우

    Examples:
        parse_term_policy("2년"):
        TermPolicy(policy_type='FIXED_DURATION', min_term=2, max_term=2, term_unit='year')

        parse_term_policy("1년, 2년, 3년"):
        TermPolicy(policy_type='CHOICES', choices=[1, 2, 3], term_unit='year')
        
        parse_term_policy("90일 이상 180일 이하"):
        TermPolicy(policy_type='RANGE', min_term=90, max_term=180, term_unit='day')
    """
    normalized_text = text.strip()

    # CASE 1: 만기일 고정 (FIXED_DATE)
    date_match = re.search(r'(\d{4})[.\s/년]+(\d{1,2})[.\s/월]+(\d{1,2})',
                           normalized_text)
    if date_match:
        year, month, day = map(int, date_match.groups())
        return TermPolicy(policy_type='FIXED_DATE',
                          maturity_date=date(year, month, day))

    matches = re.findall(r'(\d+)\s*(년|개월|일)', normalized_text)

    if not matches:
        print(f"'{text}'에서 유효한 기간(년/개월/일)을 찾을 수 없습니다.")
        return await _parse_term_policy_llm(normalized_text, client)

    unit_map: Dict[str, TermUnit] = {'년': 'year', '개월': 'month', '일': 'day'}
    detected_unit = unit_map[matches[0][1]]

    numbers = [int(m[0]) for m in matches]

    # CASE 2: 범위로 주어지는 경우 (RANGE)
    if (('이상' in normalized_text and '이하' in normalized_text) or
        (" ~ " in normalized_text)) and len(numbers) >= 2:
        return TermPolicy(policy_type='RANGE',
                          min_term=min(numbers),
                          max_term=max(numbers),
                          term_unit=detected_unit)

    # CASE 3: 선택 가능한 경우 (CHOICES)
    if (',' in normalized_text or '또는' in normalized_text) and len(numbers) > 1:
        return TermPolicy(policy_type='CHOICES',
                          choices=sorted(numbers),
                          term_unit=detected_unit)

    # CASE 4: 단일 기간 고정 (FIXED_DURATION)
    if len(numbers) == 1:
        return TermPolicy(policy_type='FIXED_DURATION',
                          min_term=numbers[0],
                          max_term=numbers[0],
                          term_unit=detected_unit)

    return await _parse_term_policy_llm(normalized_text, client)


def _text_to_amount(text: str) -> int:
    """자연어를 정수형으로 변환"""
    text = text.strip().replace(",", "").replace("원", "")

    num_part_str = re.search(r"[\d.]+", text)
    if not num_part_str:
        raise ValueError(f"숫자를 찾을 수 없습니다: '{text}'")

    num = float(num_part_str.group())

    if "억" in text:
        num *= 100_000_000
    if "만" in text:
        num *= 10_000
    if "천" in text:
        num *= 1_000

    return int(num)


@retry_async(times=10, delay=1)
async def _parse_amount_policy_llm(text: str, client: AsyncOpenAI) -> AmountPolicy:

    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "amount_policy",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "policy_type": {
                        "type": "string",
                        "enum": ["RANGE", "CHOICES", "FIXED_AMOUNT"],
                        "description": "정책 유형"
                    },
                    "min_amount": {
                        "type": "integer",
                        "description": "최소 납입 금액(원)"
                    },
                    "max_amount": {
                        "type": "integer",
                        "description": "최대 납입 금액(원)"
                    },
                    "choices": {
                        "type": "array",
                        "items": {
                            "type": "integer",
                            "description": "선택 가능한 납입 금액(원)"
                        }
                    },
                    "fixed_amount": {
                        "type": "integer",
                        "description": "고정 납입 금액(원)"
                    },
                    "amount_unit": {
                        "type": "string",
                        "enum": ["day", "month", "year"],
                        "description": "금액 납입 주기 단위"
                    }
                },
                "required": ["policy_type"]
            }
        }
    }

    SYSTEM_PROMPT = """\
    당신의 역할은 입력받은 한국어 금융상품 설명 문장에서 "납입 금액 정책(AmountPolicy)" 정보를 **JSON 객체**로만 추출하여 반환하는 것이다.  
    반환 결과는 아래 JSON Schema를 반드시 충족해야 하며, 추가,누락된 키가 존재해서는 안된다.

    - JSON Schema 요약
    {
      "policy_type": "RANGE | CHOICES | FIXED_AMOUNT",   // 필수
      "min_amount":   integer,   // RANGE
      "max_amount":   integer,   // RANGE
      "choices":      integer[], // CHOICES
      "fixed_amount": integer,   // FIXED_AMOUNT
      "amount_unit":  "day | month | year"               // 전 타입 공통
    }

    - 조건 (policy_type에 따른 필수·금지 필드)
    1. **RANGE**  
       - 반드시 `min_amount`, `max_amount`, `amount_unit`을 포함하고 `choices`, `fixed_amount`는 넣지 않는다.
    2. **CHOICES**  
       - `choices` 배열과 `amount_unit`만 포함한다.  
       - `min_amount`, `max_amount`, `fixed_amount`는 포함하지 않는다.
    3. **FIXED_AMOUNT**  
       - 오직 `fixed_amount`와 `amount_unit`만 포함한다.  
       - `min_amount`, `max_amount`, `choices`는 포함하지 않는다.

    - 공통 규칙
        - 모든 금액은 ‘원’ 단위 정수(쉼표·단위어 제거)로 기록한다.
        - `amount_unit` 값은 반드시 소문자로(day, month, year 중 하나).
    """

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": text
        },
    ]

    response = await client.chat.completions.create(
        model="solar-pro2",
        messages=messages,  # type: ignore
        response_format=schema,  # type: ignore
        max_tokens=16384,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("올바르지 않은 값입니다.")

    data = json.loads(content)

    return AmountPolicy(**data)


async def parse_amount_policy(text: str, client: AsyncOpenAI) -> AmountPolicy:
    """입력된 문자열에서 납입 금액 정책을 파싱하여 AmountPolicy 객체를 반환합니다.

    Args:
        text (str): 파싱할 납입 금액 텍스트 (예: "30만원", "1만원 이상 50만원 이하")

    Returns:
        AmountPolicy: 파싱된 납입 금액 정책 객체

    Raises:
        ValueError: 텍스트에서 유효한 정책을 찾지 못한 경우
    """
    normalized_text = text.strip()

    unit: TermUnit = "month"
    if "매일" in normalized_text or "일 " in normalized_text:
        unit = "day"
    elif "매년" in normalized_text or "연 " in normalized_text:
        unit = "year"

    # CASE 3: 납입 금액 단일값
    try:
        # CASE 1: 납입 금액 범위 지정
        if ("이상" in normalized_text and
                "이하" in normalized_text) or (" ~ " in normalized_text):
            range_match = re.search(r"(.+?)\s*이상\s*~?\s*(.+?)\s*이하", normalized_text)
            if range_match:
                min_str, max_str = range_match.groups()
                return AmountPolicy(
                    policy_type="RANGE",
                    min_amount=_text_to_amount(min_str),
                    max_amount=_text_to_amount(max_str),
                    amount_unit=unit,
                )

        # CASE 2: 납입 금액 다중 선택
        if "또는" in normalized_text or "," in normalized_text:
            # '또는' 이나 쉼표(,)를 기준으로 분리
            parts = re.split(r"\s*또는\s*|,\s*", normalized_text)
            # 분리된 각 부분에서 숫자를 추출
            amount_choices = [p for p in parts if re.search(r"\d", p)]
            if len(amount_choices) > 1:
                return AmountPolicy(
                    policy_type="CHOICES",
                    choices=sorted([_text_to_amount(s) for s in amount_choices]),
                    amount_unit=unit,
                )
            return AmountPolicy(
                policy_type="FIXED_AMOUNT",
                fixed_amount=_text_to_amount(normalized_text),
                amount_unit=unit,
            )

    except ValueError:
        print(f"'{normalized_text}' 파싱에 실패했습니다. LLM으로 전환합니다.")

    return await _parse_amount_policy_llm(normalized_text, client=client)


if __name__ == "__main__":
    test = """\
    1개월이상 24개월이하 (일 단위), 만기일은 전역(또는 소집해제) 예정일
    """

    result = parse_term_policy(test)
    print(result)

    test2 = "매일 5,000원 또는 10,000원 中 택 1 (정액식)"
    result = parse_amount_policy(test2)
    print(result)
