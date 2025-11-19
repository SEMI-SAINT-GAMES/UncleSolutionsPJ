from fastapi import FastAPI
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")
client = MongoClient(MONGO_URL)
db = client[DATABASE_NAME]
app = FastAPI()
from .routes import router

app.include_router(router)

__all__ = ["app", "db"]