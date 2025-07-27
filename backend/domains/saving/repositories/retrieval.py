from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection

from common.database import init_mongodb_client
from domains.saving.schemas import (
    SavingRateWeights,
    SavingSearchResult,
)


def build_search_pipeline(
        *,
        total_term_months: Optional[int] = None,  # 가입 기간(월)
        monthly_deposit: Optional[int] = None,  # 월 납입 금액
        target_amount: Optional[int] = None,  # 목표 금액
        top_k: int = 5,
        offset: int = 0,
        w_base: float = 0.5,  # 기본금리 가중치
        w_max: float = 0.5  # 최대금리 가중치
):
    """
    SavingSearchResult 형태로 반환하기 위한 MongoDB aggregation 파이프라인을 생성한다.
    세 파라미터 중 **정확히 두 개**만 입력해야 한다.
    """

    print(f"w_base: {w_base}, w_max: {w_max}")

    # --- 0) 파라미터 검증 ---------------------------------------------------
    supplied = [
        total_term_months is not None, monthly_deposit is not None, target_amount
        is not None
    ]
    if supplied.count(True) != 2:
        raise ValueError("세 파라미터 중 정확히 두 개만 지정해야 합니다.")

    # 파라미터를 $literal 로 감싸야 파이프라인 안에서 사용 가능
    lt = lambda v: {"$literal": v} if v is not None else v

    # --- 1) 기본 금리(baseRate) 추출(가입 기간 반영) -------------------------
    base_rate_stage = {
        "$set": {
            "baseRate": {
                "$cond": [
                    {
                        "$isArray": "$base_interest_rate"
                    },
                    {
                        "$let": {
                            "vars": {
                                "tier": {
                                    "$first": {
                                        "$filter": {
                                            "input": "$base_interest_rate",
                                            "as": "t",
                                            "cond": {
                                                "$and": [
                                                    # min_term ≤ term_months
                                                    {
                                                        "$lte": [
                                                            "$$t.min_term",
                                                            lt(total_term_months) or
                                                            "$_termMonths"
                                                        ]
                                                    },
                                                    # term_months < max_term  (또는 max_term 없음)
                                                    {
                                                        "$or": [{
                                                            "$eq": [
                                                                "$$t.max_term", None
                                                            ]
                                                        }, {
                                                            "$gt": [
                                                                "$$t.max_term",
                                                                lt(total_term_months) or
                                                                "$_termMonths"
                                                            ]
                                                        }]
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }
                            },
                            "in": "$$tier.interest_rate"
                        }
                    },
                    "$base_interest_rate"
                ]
            }
        }
    }

    # --- 2) 모자란 파라미터 보간 ------------------------------------------
    #
    #  · term_months가 None  →  ceil(goal_amount / monthly_amount)
    #  · monthly_amount가 None → ceil(goal_amount / term_months)
    #  · goal_amount가 None  →  monthly_amount * term_months
    #
    fill_stage = {"$set": {}}

    if total_term_months is None:
        fill_stage["$set"]["_termMonths"] = {
            "$ceil": {
                "$divide": [lt(target_amount), lt(monthly_deposit)]
            }
        }
        fill_stage["$set"]["_monthlyAmount"] = lt(monthly_deposit)
        fill_stage["$set"]["_goalAmount"] = lt(target_amount)

    elif monthly_deposit is None:
        fill_stage["$set"]["_termMonths"] = lt(total_term_months)
        fill_stage["$set"]["_monthlyAmount"] = {
            "$ceil": {
                "$divide": [lt(target_amount), lt(total_term_months)]
            }
        }
        fill_stage["$set"]["_goalAmount"] = lt(target_amount)

    else:  # goal_amount is None
        fill_stage["$set"]["_termMonths"] = lt(total_term_months)
        fill_stage["$set"]["_monthlyAmount"] = lt(monthly_deposit)
        fill_stage["$set"]["_goalAmount"] = {
            "$multiply": [lt(monthly_deposit),
                          lt(total_term_months)]
        }
    # --- 2.5) 가입 기간 및 납입 금액 필터링 -------------------------------
    term_expr = {
        "$or": [
            # RANGE 또는 FIXED_DURATION
            {
                "$and": [{
                    "$in": ["$term.policy_type", ["RANGE", "FIXED_DURATION"]]
                }, {
                    "$gte": ["$_termMonths", "$term.min_term"]
                }, {
                    "$or": [{
                        "$eq": ["$term.max_term", None]
                    }, {
                        "$lte": ["$_termMonths", "$term.max_term"]
                    }]
                }]
            },
            # CHOICES (배열인지 확인 후에만 $in)
            {
                "$and": [{
                    "$eq": ["$term.policy_type", "CHOICES"]
                }, {
                    "$isArray": "$term.choices"
                }, {
                    "$in": ["$_termMonths", "$term.choices"]
                }]
            },
            # FIXED_DATE
            {
                "$eq": ["$term.policy_type", "FIXED_DATE"]
            }
        ]
    }

    # --- 납입 금액(amount) 필터 조건 정의 -------------------------------
    amount_expr = {
        "$or": [
            # RANGE
            {
                "$and": [{
                    "$eq": ["$amount.policy_type", "RANGE"]
                }, {
                    "$gte": ["$_monthlyAmount", "$amount.min_amount"]
                }, {
                    "$or": [{
                        "$eq": ["$amount.max_amount", None]
                    }, {
                        "$lte": ["$_monthlyAmount", "$amount.max_amount"]
                    }]
                }]
            },
            # CHOICES (배열인지 확인 후에만 $in)
            {
                "$and": [{
                    "$eq": ["$amount.policy_type", "CHOICES"]
                }, {
                    "$isArray": "$amount.choices"
                }, {
                    "$in": ["$_monthlyAmount", "$amount.choices"]
                }]
            },
            # FIXED_AMOUNT
            {
                "$and": [{
                    "$eq": ["$amount.policy_type", "FIXED_AMOUNT"]
                }, {
                    "$eq": ["$_monthlyAmount", "$amount.fixed_amount"]
                }]
            }
        ]
    }
    filter_stage = {"$match": {"$expr": {"$and": [term_expr, amount_expr]}}}

    # --- 3) 원금·이자 계산 --------------------------------------------------
    calc_fin_stage = {
        "$addFields": {
            "principal": {
                "$multiply": ["$_monthlyAmount", "$_termMonths"]
            },
        }
    }

    calc_interest_stage = {
        "$addFields": {
            "interest": {
                "$divide": [{
                    "$multiply": [
                        "$principal", {
                            "$ifNull": ["$baseRate", 0]
                        }, {
                            "$divide": ["$_termMonths", 12]
                        }
                    ]
                }, 100]
            }
        }
    }

    # --- 4) 금리 정규화·가중합 점수 ----------------------------------------
    stats_facet = {
        "$facet": {
            "stats": [{
                "$group": {
                    "_id": 0,
                    "minBase": {
                        "$min": "$baseRate"
                    },
                    "maxBase": {
                        "$max": "$baseRate"
                    },
                    "minMax": {
                        "$min": "$max_interest_rate"
                    },
                    "maxMax": {
                        "$max": "$max_interest_rate"
                    }
                }
            }],
            "docs": [{
                "$match": {}
            }]
        }
    }

    unwind_stats = [{
        "$unwind": "$stats"
    }, {
        "$unwind": "$docs"
    }, {
        "$replaceRoot": {
            "newRoot": {
                "$mergeObjects": ["$stats", "$docs"]
            }
        }
    }]

    norm = {
        "$addFields": {
            "normBase": {
                "$cond": [{
                    "$eq": ["$maxBase", "$minBase"]
                }, 0, {
                    "$divide": [{
                        "$subtract": ["$baseRate", "$minBase"]
                    }, {
                        "$subtract": ["$maxBase", "$minBase"]
                    }]
                }]
            },
            "normMax": {
                "$cond": [{
                    "$eq": ["$maxMax", "$minMax"]
                }, 0, {
                    "$divide": [{
                        "$subtract": ["$max_interest_rate", "$minMax"]
                    }, {
                        "$subtract": ["$maxMax", "$minMax"]
                    }]
                }]
            },
        }
    }

    score = {
        "$addFields": {
            "score": {
                "$add": [{
                    "$multiply": ["$normBase", w_base]
                }, {
                    "$multiply": ["$normMax", w_max]
                }]
            }
        }
    }

    # --- 5) 금리 순위(base_rate_rank, max_rate_rank) -----------------------
    rank_base = {
        "$setWindowFields": {
            "sortBy": {
                "baseRate": -1
            },
            "output": {
                "base_rate_rank": {
                    "$rank": {}
                }
            }
        }
    }

    rank_max = {
        "$setWindowFields": {
            "sortBy": {
                "max_interest_rate": -1
            },
            "output": {
                "max_rate_rank": {
                    "$rank": {}
                }
            }
        }
    }

    # 완성된 파이프라인
    full_stages = [
        fill_stage,
        filter_stage,
        base_rate_stage,
        calc_fin_stage,
        calc_interest_stage,
        stats_facet,
        *unwind_stats,
        norm,
        score,
        rank_base,
        rank_max,
        {
            "$sort": {
                "score": -1
            }
        },
    ]

    full_stages += [{"$skip": offset}, {"$limit": top_k}]

    return full_stages


async def find_savings(
    collection: AsyncIOMotorCollection,
    weights: SavingRateWeights,
    target_amount: Optional[int] = None,
    monthly_deposit: Optional[int] = None,
    total_term_months: Optional[int] = None,
    top_k: int = 5,
    offset: int = 0,
) -> List[SavingSearchResult]:

    pipeline = build_search_pipeline(target_amount=target_amount,
                                     monthly_deposit=monthly_deposit,
                                     total_term_months=total_term_months,
                                     top_k=top_k,
                                     w_base=weights.base,
                                     w_max=weights.max,
                                     offset=offset)

    try:
        cursor = collection.aggregate(pipeline)
        raw_datas = await cursor.to_list()
        savings = [SavingSearchResult(**raw) for raw in raw_datas]

        return savings

    except Exception as e:
        raise RuntimeError(f"적금 검색에 실패했습니다: {e}") from e


async def _test():

    _, db = init_mongodb_client()
    collection = db.get_collection("savings")

    weights = SavingRateWeights(base=0.3, max=0.3)
    #target_amount = 3_000_000
    monthly_deposit = 100_000
    total_term_months = 12
    top_k = 10

    try:
        results = await find_savings(
            collection=collection,
            weights=weights,
            monthly_deposit=monthly_deposit,
            total_term_months=total_term_months,
            top_k=top_k,
        )

        print("적금 검색 결과:")
        for idx, result in enumerate(results, 1):
            print(
                f"{idx}. {result.product.name} ({result.product.institution}) 최대 금리 {result.product.max_interest_rate}% , 기본 금리 {result.product.base_interest_rate}%, 원금 {result.principal}, 이자 {result.interest}"
            )

    except Exception as e:
        print("테스트 실패:", e)


import asyncio

if __name__ == "__main__":
    asyncio.run(_test())
