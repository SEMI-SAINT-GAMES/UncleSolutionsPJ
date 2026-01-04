import os

from pymongo.asynchronous.mongo_client import AsyncMongoClient

mongodb_client: AsyncMongoClient | None = None
mongodb = None


async def connect_to_mongo() -> AsyncMongoClient | None:
    print("Connecting to MongoDB...")
    print(os.getenv("MONGO_URL"))
    global mongodb_client, mongodb
    if mongodb_client is None:
        try:
            mongodb_client = AsyncMongoClient(os.getenv("MONGO_URL"))
            mongodb = mongodb_client[os.getenv("MONGO_DB_NAME")]
            print("Connected to MongoDB!")
            print(mongodb)
            return mongodb
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise e


async def close_mongo():
    global mongodb_client
    if mongodb_client:
        await mongodb_client.close()
        print("MongoDB connection closed")


async def get_mongodb() -> AsyncMongoClient | None:
    global mongodb
    if mongodb is None:
        mongodb = await connect_to_mongo()
    return mongodb
