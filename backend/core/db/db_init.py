from contextlib import asynccontextmanager

from core.db.mongo import close_mongo, connect_to_mongo
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await connect_to_mongo()
    yield
    await close_mongo()
