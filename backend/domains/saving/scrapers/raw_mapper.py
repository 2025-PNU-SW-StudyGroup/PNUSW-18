import asyncio, json
from pathlib import Path
from typing import List

from tqdm import tqdm

from motor.motor_asyncio import AsyncIOMotorCollection
import uvloop
from openai import AsyncOpenAI

from common.database import init_mongodb_client
from domains.saving.models import Saving

from domains.saving.repositories.mutations import insert_savings
from domains.saving.scrapers.parsers import (
    parse_term_policy,
    parse_amount_policy,
)

from domains.saving.scrapers.extractors import (
    extract_base_interest_rate_tiers,
    extract_saving_preferential_rates,
)

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

import re


async def raw2saving(raw: dict, client: AsyncOpenAI) -> Saving:

    data = {
        "name": raw["basic_info"]["title"],
        "institution": raw["basic_info"]["institution"],
        "targets": raw["product_guide"].get("targets", "-"),
        "enroll_method": raw["product_guide"].get("enroll_method", "fixed"),
        "event": raw["basic_info"].get("enroll_method", None)
    }

    tasks = {}

    tasks["term"] = asyncio.create_task(
        parse_term_policy(raw["product_guide"]["term"], client=client))
    tasks["amount"] = asyncio.create_task(
        parse_amount_policy(raw["product_guide"]["amount"], client=client))

    def extract_percentages(text: str) -> float:
        """XX.XX% -> XX.XX"""
        pattern = r"(\d+(?:\.\d{1,2})?)%"
        temp = re.findall(pattern, text)
        if not temp:
            raise ValueError(f"{text}를 숫자로 변환하지 못했습니다.")

        return float(temp[0])

    if hasattr(raw["interest_rate_guide"], "interest_rate_per_terms"):
        html_table = raw["interest_rate_guide"]["interest_rate_per_terms"]
        tasks["base_interest_rate"] = asyncio.create_task(
            extract_base_interest_rate_tiers(client, html_table))

    else:

        raw_interest_rate: str = raw["basic_info"]["base_interest_rate"]
        data["base_interest_rate"] = extract_percentages(raw_interest_rate)

    data["max_interest_rate"] = extract_percentages(
        raw["basic_info"]["max_interest_rate"])

    if "conditions" in raw["interest_rate_guide"]:
        conditions = raw["interest_rate_guide"]["conditions"]

        _tasks = [
            asyncio.create_task(extract_saving_preferential_rates(client, text))
            for text in conditions
        ]
        tasks["preferential_rates"] = asyncio.gather(*_tasks)

    raw_interest_type = raw["interest_rate_guide"].get("interest_type", "고정금리")
    data["interest_type"] = "fixed" if raw_interest_type == "고정금리" else "variable"

    raw_earn_method = raw["product_guide"].get("earn_method", "정액적립식")
    data["earn_method"] = "flexible" if "자유" in raw_earn_method else "fixed"

    data = {**data, **{key: await task for key, task in tasks.items()}}

    if "preferential_rates" not in data:
        data["preferential_rates"] = []

    saving = Saving(**data)
    print(f"\n====== {saving.name} ======")
    print(f"최대 금리: {saving.format_interest_rates()}")
    print(f"기본 금리: {saving.base_interest_rate}")

    return Saving(**data)


UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")

INPUT_PATH = Path("savings.jsonl")
OUTPUT_PATH = Path("data/savings_parsed.jsonl")
MODEL = "solar-pro"
MAX_CONCURRENCY = 1


async def parse_raw_datas(openai_client: AsyncOpenAI):

    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    raw_datas = []
    with open(INPUT_PATH, "r", encoding="utf-8") as fp:
        for line in fp:
            raw_datas.append(line)

    async def convert(line: str) -> Saving:
        raw = json.loads(line, strict=False)
        async with sem:
            return await raw2saving(raw, openai_client)

    tasks = [asyncio.create_task(convert(line)) for line in raw_datas]
    #savings: List[Saving] = await asyncio.gather(*(convert(data) for data in raw_datas))
    savings: List[Saving] = []

    #result = await insert_savings(saving_collection, savings)
    for fut in tqdm(asyncio.as_completed(tasks), total=len(raw_datas), desc="Parsing"):
        savings.append(await fut)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as fp:
        for saving in savings:
            json_str = saving.model_dump_json()
            fp.write(json_str + "\n")

    return savings


async def insert_datas(saving_collection: AsyncIOMotorCollection,
                       savings: List[Saving]):

    result = await saving_collection.delete_many({})
    print(f"Deleted {result.deleted_count} documents.")
    """
    raw_datas: List[str] = []
    with open(OUTPUT_PATH, "r", encoding="utf-8") as fp:
        for line in fp:
            raw_datas.append(line)

    def convert(line: str) -> Saving:
        raw = json.loads(line, strict=False)
        return Saving(**raw)

    savings: List[Saving] = list(map(convert, raw_datas))
    """
    result = await insert_savings(saving_collection, savings)

    print(f"{len(result['ids'])} rows added")


async def run():

    uvloop.install()

    _, database = init_mongodb_client()

    openai_client = AsyncOpenAI(
        api_key=UPSTAGE_API_KEY,
        base_url="https://api.upstage.ai/v1",
    )

    savings = await parse_raw_datas(openai_client)
    saving_collection = database.get_collection("savings")
    result = await insert_datas(saving_collection, savings)

    print(result)


if __name__ == "__main__":

    asyncio.run(run())
