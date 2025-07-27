from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorDatabase


def get_database(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.database


def get_workflow_stream(request: Request):
    return request.app.state.graph
