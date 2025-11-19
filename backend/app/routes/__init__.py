#
# from .user_routes import user_router
# from .auth_routes import auth_router
# from main import app
# from fastapi import APIRouter, HTTPException, FastAPI
# from motor.motor_asyncio import AsyncIOMotorClient
# from contextlib import asynccontextmanager
# import os
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await startup_db_client()
#     yield
#     await shutdown_db_client()
#
# async def startup_db_client():
#     app.mongodb_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
#     app.mongodb = app.mongodb_client.get_database(os.getenv("DATABASE_NAME"))
#     print("Connected to the MongoDB database!")
#
# async def shutdown_db_client():
#     app.mongodb_client.close()
#     print("Disconnected from the MongoDB database!")
#
#
# router = APIRouter()
# router.include_router(user_router)
# router.include_router(auth_router)