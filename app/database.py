from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = str(os.getenv("MONGO_URI"))
client = AsyncIOMotorClient(MONGO_URI)
db = client.get_database(str(os.getenv("MONGO_DB")))
