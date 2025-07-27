from typing import Tuple
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_HOST = os.getenv("MONGODB_HOST", "")
MONGODB_PORT = os.getenv("MONGODB_PORT", "")
MONGODB_USER = os.getenv("MONGODB_USER", "")
MONGODB_PWD = os.getenv("MONGODB_PWD", "")
MONGODB_DBNAME = os.getenv("MONGODB_DBNAME", "")


def init_mongodb_client(
    user: str = MONGODB_USER,
    pwd: str = MONGODB_PWD,
    host: str = MONGODB_HOST,
    port: str = MONGODB_PORT,
    dbname: str = MONGODB_DBNAME,
) -> Tuple[AsyncIOMotorClient, AsyncIOMotorDatabase]:
    """MongoDB 클라이언트 초기 설정"""

    uri = f"mongodb://{user}:{pwd}@{host}:{port}/{dbname}?authSource=admin"
    client = AsyncIOMotorClient(uri)

    database = client.get_database(dbname)

    return client, database
