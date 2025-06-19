import motor.motor_asyncio
from utils.logger import log
from utils.config import Config
from typing import Optional


# from bson import ObjectId
# 
# class MongoDBHandler:
#     def __init__(self, config: Config):
#         mongo_url = f"mongodb://{config.db.username}:{config.db.password}@{config.db.ip}:{config.db.port}"
#         self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
#         self.database = self.client[config.db.db_name]
        
class MongoDBHandler:
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.database = None

    async def __aenter__(self):
        mongo_url = f"mongodb://{self.config.db.username}:{self.config.db.password}@{self.config.db.ip}:{self.config.db.port}"
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        self.database = self.client[self.config.db.db_name]

        try:
            await self.client.admin.command("ping")
            log.info("✅ MongoDB connection established.")
        except Exception as e:
            log.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        log.info("🛑 MongoDB connection closed.")

    async def update_latest_processed_block(self, height: int, time: str) -> bool:
        collection = self.database['blocks']

        if not isinstance(height, int) or height < 0:
            log.warning(f"Invalid block height: {height}")
            raise ValueError(f"Invalid block height: {height}")

        existing = await collection.find_one({'_id': 'lock'})
        if existing:
            current = existing.get('latest_processed_block', 0)
            if height <= current:
                log.warning(f"Ignored outdated height update: {height} <= {current}")
                raise Exception
            
        await collection.update_one(
            {'_id': 'lock'},
            {'$set': {
                'latest_processed_block': height,
                'latest_processed_block_time': time
            }},
            upsert=True
        )
        log.info(f"Updated latest_processed_block to {height}")


    async def get_latest_processed_block(self) -> dict:
        """ Returns {'height': int, 'time': 'YYYY-MM-DD'} """
        collection = self.database['blocks']
        lock = await collection.find_one({'_id': 'lock'})
        if lock:
            return {
                'height': int(lock['latest_processed_block']),
                'time':   lock['latest_processed_block_time']
            }
        
        return {'height': 0, 'time': None}
        
    async def insert_daily_validator_stats(self, date: str, date_end_height: int, date_start_height: int, stats: dict):
        """Writes one document per day of aggregated validator metrics."""
        collection = self.database['daily_validator_stats']
        await collection.insert_one({
            '_id': date,
            'date_start_height': date_start_height,
            'date_end_height': date_end_height,
            'validators': stats,
        })
