import motor.motor_asyncio
from utils.logger import log
from utils.config import Config
from pymongo.errors import DuplicateKeyError

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

    async def update_latest_processed_block(self, height: int, time: str, chain_id: str) -> bool:
        collection = self.database['lock']

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
                'latest_processed_block_time': time,
                'chain_id': chain_id
            }},
            upsert=True
        )
        log.info(f"Updated latest_processed_block to {height}")

    async def get_latest_processed_block(self) -> dict:
        """ Returns {'height': int, 'time': 'YYYY-MM-DD'} """
        collection = self.database['lock']
        lock = await collection.find_one({'_id': 'lock'})
        if lock:
            return {
                'height': int(lock['latest_processed_block']),
                'time':   lock['latest_processed_block_time'],
                'chain_id':   lock['chain_id'],
            }
        
    async def insert_daily_validator_stats(self, date: str, date_end_height: int, date_start_height: int, stats: dict):
        """Writes one document per day of aggregated validator metrics."""
        collection = self.database['daily_validator_stats']
        await collection.insert_one({
            '_id': date,
            'date_start_height': date_start_height,
            'date_end_height': date_end_height,
            'validators': stats,
        })

        log.info(f"Inserted validator_stats for {date} ({date_start_height} -> {date_start_height})")

    async def get_validator_stats_days(self) -> list[dict]:
        collection = self.database['daily_validator_stats']
        cursor = collection.find({})
        docs = await cursor.to_list(length=None)
        log.info(f"Fetched {len(docs)} days")
        return docs

    async def add_validator_slash(self, date: str, height: int, valoper: str):
        collection = self.database['slashes']
        existing = await collection.find_one({'_id': valoper})
        if existing:
            inserted_slashes = existing['slashes']
            for slash in inserted_slashes:
                if slash['height'] == height:
                    log.info(f"Slash already exists for {valoper}. Skipping inserting")
                    return

        await collection.update_one(
            {'_id': valoper},
            {
                '$push': {
                    'slashes': {
                        'height': height,
                        'date': date
                    }
                }
            },
            upsert=True
        )
        log.info(f"Inserted new slash for {valoper} at height {height}")

    async def get_slashes(self) -> list[dict]:
        collection = self.database['slashes']
        cursor = collection.find({})
        docs = await cursor.to_list(length=None)
        log.info(f"Fetched {len(docs)} slashes")
        return docs
    
    async def get_processed_proposals(self) -> list[dict]:
        collection = self.database['governance']
        cursor = collection.find({})
        docs = await cursor.to_list(length=None)
        log.info(f"Fetched {len(docs)} processed proposals")
        return docs

    async def update_validator_vote(
        self,
        proposal_id: int,
        valoper: str,
        option: str,
        tx_height: int,
        tx_hash: str
    ):
        collection = self.database['governance']

        await collection.update_one(
            {'_id': proposal_id},
            {
                '$set': {
                    f'validators.{valoper}': {
                        'option': option,
                        'tx_height': tx_height,
                        'tx_hash': tx_hash,
                    }
                }
            },
            upsert=True
        )
        log.info(
            f"Recorded vote for proposal {proposal_id}, validator {valoper}: "
            f"{option} (tx {tx_hash} @ {tx_height})"
        )

    async def inserts_proposal(self, proposal_id: int):
        collection = self.database['governance']
        doc = {
            "_id": proposal_id,
            "validators": {}
        }
        try:
            result = await collection.insert_one(doc)
            return result
        except DuplicateKeyError:
            self.logger.info(f"Proposal {proposal_id!r} already exists, skipping insert.")
    