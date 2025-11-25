from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi
from config import settings


class Database:
    client: AsyncMongoClient = None


db = Database()


async def get_db_connection():
    """
    Get database connection
    """
    if db.client is None:
        mongodb_uri = settings.MONGODB_URI
        if not mongodb_uri:
            raise Exception("MONGODB_URI environment variable not set.")

        db.client = AsyncMongoClient(mongodb_uri, server_api=ServerApi('1'))
    return db.client["shutdown_schedule"]


async def close_db_connection():
    """
    Close database connection
    """
    if db.client:
        await db.client.close()
