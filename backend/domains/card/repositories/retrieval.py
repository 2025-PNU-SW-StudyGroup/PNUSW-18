from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection

from domains.saving.schemas import (
    SavingRateWeights,
    SavingSearchResult,
)


async def search_savings(
    collection: AsyncIOMotorCollection,
    weights: SavingRateWeights,
    monthly_deposit: Optional[int] = None,
    target_amount: Optional[int] = None,
    total_term_months: Optional[int] = None,
) -> List[SavingSearchResult]:
    """다중 조건과 Weighted Sum을 결합한 통합 적금 상품 검색 수행.

    Args:
        collection: MongoDB 'savings' 컬렉션 객체
        monthly_deposit (Optional[int]): 월 납입 희망 금액.
        target_amount (Optional[int]): 목표 금액. 월 납입액과 함께 주어지면 도달 기간 계산.
        total_term_months (Optional[int]): 총 납입 기간(개월). 주어지면 상품 필터링 적용 및 만기 금액 계산.
        k (int): RRF 랭킹 가중치 상수

    Returns:
        List[dict]: 하이브리드 랭킹 순으로 정렬된 상품 목록. 조건에 따라 추가 계산 결과가 포함됩니다.
    """
    pipeline = []

    # 1. 동적 필터링 ($match)
    match_filter = {}
    if monthly_deposit is not None:
        match_filter.update({
            "min_amount": {
                "$lte": monthly_deposit
            },
            "max_amount": {
                "$gte": monthly_deposit
            },
        })
    if total_term_months is not None:
        match_filter.update({
            "min_term": {
                "$lte": total_term_months
            },
            "max_term": {
                "$gte": total_term_months
            },
        })

    if match_filter:
        pipeline.append({"$match": match_filter})

    # 2. 금리 유형 계산 ($addFields)
    pipeline.append({
        "$addFields": {
            "max_interest_rate": {
                "$add": [
                    "$base_interest_rate", {
                        "$sum": "$preferential_rates.interest_rate"
                    }
                ]
            },
            "intermediate_interest_rate": {
                "$add": [
                    "$base_interest_rate", {
                        "$sum": {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$preferential_rates",
                                        "as": "rate",
                                        "cond": {
                                            "$eq": ["$$rate.rate_type", "user_choice"]
                                        }
                                    }
                                },
                                "as": "filtered_rate",
                                "in": "$$filtered_rate.interest_rate"
                            }
                        }
                    }
                ]
            }
        }
    })

    # 3. 조건부 금융 계산 ($addFields)
    financial_calculations = {}

    # 3. 정규화를 위한 각 금리별 min/max 값 계산 ($facet)
    pipeline.append({
        "$facet": {
            "stats": [{
                "$group": {
                    "_id": None,
                    "min_base": {
                        "$min": "$base_interest_rate"
                    },
                    "max_base": {
                        "$max": "$base_interest_rate"
                    },
                    "min_max": {
                        "$min": "$max_interest_rate"
                    },
                    "max_max": {
                        "$max": "$max_interest_rate"
                    },
                    "min_intermediate": {
                        "$min": "$intermediate_interest_rate"
                    },
                    "max_intermediate": {
                        "$max": "$intermediate_interest_rate"
                    }
                }
            }],
            "documents": [{
                "$match": {}
            }]  # 모든 문서를 그대로 전달
        }
    })

    # 4. 통계 데이터(stats)를 각 문서에 결합
    pipeline.extend([{
        "$unwind": "$documents"
    }, {
        "$addFields": {
            "documents.stats": {
                "$arrayElemAt": ["$stats", 0]
            }
        }
    }, {
        "$replaceRoot": {
            "newRoot": "$documents"
        }
    }])

    # 5. 정규화 및 가중합 점수 계산
    pipeline.append({
        "$addFields": {
            # Min-Max Normalization: (value - min) / (max - min)
            "normalized_base": {
                "$cond": [{
                    "$eq": ["$stats.max_base", "$stats.min_base"]
                }, 0, {
                    "$divide": [{
                        "$subtract": ["$base_interest_rate", "$stats.min_base"]
                    }, {
                        "$subtract": ["$stats.max_base", "$stats.min_base"]
                    }]
                }]
            },
            "normalized_max": {
                "$cond": [{
                    "$eq": ["$stats.max_max", "$stats.min_max"]
                }, 0, {
                    "$divide": [{
                        "$subtract": ["$max_interest_rate", "$stats.min_max"]
                    }, {
                        "$subtract": ["$stats.max_max", "$stats.min_max"]
                    }]
                }]
            },
            "normalized_intermediate": {
                "$cond": [{
                    "$eq": ["$stats.max_intermediate", "$stats.min_intermediate"]
                }, 0, {
                    "$divide": [{
                        "$subtract": [
                            "$intermediate_interest_rate", "$stats.min_intermediate"
                        ]
                    }, {
                        "$subtract": [
                            "$stats.max_intermediate", "$stats.min_intermediate"
                        ]
                    }]
                }]
            },
        }
    })

    pipeline.append({
        "$addFields": {
            "weighted_score": {
                "$add": [{
                    "$multiply": [
                        "$normalized_base",
                        weights.base,
                    ]
                }, {
                    "$multiply": [
                        "$normalized_max",
                        weights.max,
                    ]
                }, {
                    "$multiply": [
                        "$normalized_intermediate",
                        weights.intermediate,
                    ]
                }]
            }
        }
    })

    # 만기 금액 계산 (월 납입액, 기간 모두 존재 시)
    if monthly_deposit is not None and total_term_months is not None:
        total_principal = monthly_deposit * total_term_months
        financial_calculations["maturity_details"] = {
            # 월 복리 계산 공식: P * [((1 + r)^n - 1) / r]
            # r = 월이율, n = 개월 수, P = 월 납입액
            "base_rate": {
                "total_amount": {
                    "$function": {
                        "body":
                            "function(P, r_annual, n) { const r = r_annual / 12 / 100; if (r === 0) return P * n; return P * (Math.pow(1 + r, n) - 1) / r; }",
                        "args": [
                            monthly_deposit, "$base_interest_rate", total_term_months
                        ],
                        "lang":
                            "js"
                    }
                },
                "principal": total_principal,
                "interest": {
                    "$function": {
                        "body":
                            "function(P, r_annual, n) { const r = r_annual / 12 / 100; const total = (r === 0) ? P * n : P * (Math.pow(1 + r, n) - 1) / r; return total - (P * n); }",
                        "args": [
                            monthly_deposit, "$base_interest_rate", total_term_months
                        ],
                        "lang":
                            "js"
                    }
                },
            },
            "max_rate": {
                # ... max_rate, intermediate_rate 에 대해서도 동일한 로직 적용 ...
                "total_amount": {
                    "$function": {
                        "body": "...",
                        "args": [
                            monthly_deposit, "$max_interest_rate", total_term_months
                        ],
                        "lang": "js"
                    }
                },
                "interest": {
                    "$function": {
                        "body": "...",
                        "args": [
                            monthly_deposit, "$max_interest_rate", total_term_months
                        ],
                        "lang": "js"
                    }
                },
                "principal": total_principal,
            },
            "intermediate_rate": {
                "total_amount": {
                    "$function": {
                        "body": "...",
                        "args": [
                            monthly_deposit, "$intermediate_interest_rate",
                            total_term_months
                        ],
                        "lang": "js"
                    }
                },
                "interest": {
                    "$function": {
                        "body": "...",
                        "args": [
                            monthly_deposit, "$intermediate_interest_rate",
                            total_term_months
                        ],
                        "lang": "js"
                    }
                },
                "principal": total_principal,
            }
        }

    # 목표 금액 도달 기간 계산 (월 납입액, 목표액 모두 존재 시)
    if monthly_deposit is not None and target_amount is not None:
        financial_calculations["target_details"] = {
            # 기간 계산 공식 (로그 활용): n = log(1 + (FV * r) / P) / log(1 + r)
            # 최고 금리(max_rate) 기준으로 가장 빠른 도달 기간 계산
            "months_to_target": {
                "$function": {
                    "body":
                        "function(FV, P, r_annual) { const r = r_annual / 12 / 100; if (r === 0) return FV / P; return Math.log(1 + (FV * r) / P) / Math.log(1 + r); }",
                    "args": [target_amount, monthly_deposit, "$max_interest_rate"],
                    "lang":
                        "js"
                }
            },
            "total_interest": {
                "$function": {
                    "body":
                        "function(FV, P, r_annual) { const r = r_annual / 12 / 100; const n = (r === 0) ? FV / P : Math.log(1 + (FV * r) / P) / Math.log(1 + r); return FV - (P * n); }",
                    "args": [target_amount, monthly_deposit, "$max_interest_rate"],
                    "lang":
                        "js"
                }
            }
        }

    if financial_calculations:
        financial_calculations["maturity_details"]["max_rate"]["total_amount"][
            "body"] = financial_calculations["maturity_details"]["base_rate"][
                "total_amount"]["body"]
        financial_calculations["maturity_details"]["max_rate"]["interest"][
            "body"] = financial_calculations["maturity_details"]["base_rate"][
                "interest"]["body"]
        financial_calculations["maturity_details"]["intermediate_rate"]["total_amount"][
            "body"] = financial_calculations["maturity_details"]["base_rate"][
                "total_amount"]["body"]
        financial_calculations["maturity_details"]["intermediate_rate"]["interest"][
            "body"] = financial_calculations["maturity_details"]["base_rate"][
                "interest"]["body"]
        pipeline.append({"$addFields": financial_calculations})

    # 6. 최종 정렬 및 불필요한 필드 제거
    pipeline.extend([{
        "$sort": {
            "weighted_score": -1
        }
    }, {
        "$project": {
            "stats": 0,
            "normalized_base": 0,
            "normalized_max": 0,
            "normalized_intermediate": 0
        }
    }])

    cursor = collection.aggregate(pipeline)
    documents = await cursor.to_list(length=None)

    return [SavingSearchResult(**doc) for doc in documents]
