from typing import List
from motor.motor_asyncio import AsyncIOMotorCollection

from domains.saving.models import Saving


async def insert_saving(
    collection: AsyncIOMotorCollection,
    saving: Saving,
):
    """단일 적금 생성."""
    result = await collection.insert_one(saving)
    return {"id": result.inserted_id}


async def insert_savings(
    collection: AsyncIOMotorCollection,
    savings: List[Saving],
):
    """적금 다중 생성"""

    payload = [saving.model_dump(by_alias=True) for saving in savings]
    results = await collection.insert_many(payload)

    return {"ids": results.inserted_ids}
