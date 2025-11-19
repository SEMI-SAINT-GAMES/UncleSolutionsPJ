import os
from pymongo import MongoClient


client = MongoClient(os.getenv("MONGO_URL"))
db = client[os.getenv("DATABASE_NAME")]