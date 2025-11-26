from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.db.mongo import connect_to_mongo, close_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await connect_to_mongo()
    yield
    await close_mongo()
