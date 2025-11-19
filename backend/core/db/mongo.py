import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

mongodb_client: AsyncIOMotorClient | None = None
mongodb: AsyncIOMotorDatabase | None = None
async def connect_to_mongo():
    print("Connecting to MongoDB...")
    print(os.getenv("MONGO_URL"))
    global mongodb_client, mongodb
    if mongodb_client is None:
        try:
            mongodb_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
            mongodb = mongodb_client[os.getenv("DATABASE_NAME")]
            print("Connected to MongoDB!")
            print(mongodb)
            return mongodb
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise e

async def close_mongo():
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("MongoDB connection closed")

async def get_mongodb() -> AsyncIOMotorDatabase:
    global mongodb
    if mongodb is None:
        await connect_to_mongo()
    return mongodb




