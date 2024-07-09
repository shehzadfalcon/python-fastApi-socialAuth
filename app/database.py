"""
This module initializes the connection to a MongoDB database using the Motor
asyncio MongoDB driver and environment variables for configuration.
"""

from motor.motor_asyncio import AsyncIOMotorClient
import os

# Load environment variables for MongoDB URI and database name
MONGO_URI = str(os.getenv("MONGO_URI"))
"""
str: The MongoDB connection URI, loaded from environment variables.
"""

client = AsyncIOMotorClient(MONGO_URI)
"""
AsyncIOMotorClient: An instance of the Motor async MongoDB client.
"""

db = client.get_database(str(os.getenv("MONGO_DB")))
"""
Database: The MongoDB database instance, connected to the database name
specified in the environment variables.
"""
