import asyncio
import yaml
import traceback
import os

from sys import exit

from utils.logger import log
from utils.args import args
from utils.config import Config

from src.aio_calls import AioHttpCalls
from src.decoder import KeysUtils
from src.extension import ExtensionParser
from src.mongodb import MongoDBHandler
from multiprocessing import Pool

class App:
    def __init__(
        self,
        config: Config,
        aio_session: AioHttpCalls,
        mongo: MongoDBHandler
    ):
        self.aio_session = aio_session
        self.mongo = mongo
        self.config = config

        self.validators = {}
        self.rpc_lowest_height = None
        self.rpc_lowest_date = None

        self.app_end_height = None
        self.app_end_date = None

        self.app_start_height = None
        self.app_start_date = None

        self.app_current_date = None
        self.app_current_height = None

        self.day_start_height = None


        self.app_blocks_batch_size = None
        self.app_sleep_between_blocks_batch = None

    async def check_rpc_status(self):
        """Checks the RPC connection to ensure it is online."""
        status = await self.aio_session.get_rpc_status()
        if not status:
            log.error(f"Failed to connect to {self.config.rpc}. Ensure the RPC URL format is correct and the node is online.")
            exit(5)

        catching_up = status['sync_info']['catching_up']
        latest_block_height = status['sync_info']['latest_block_height']
        latest_block_time = status['sync_info']['latest_block_time']
        chain_id = status['node_info']['network']
        tx_index = status['node_info']['other']['tx_index']
        self.rpc_latest_height = int(latest_block_height)

        rpc_lowest_height = await self.aio_session.get_rpc_lowest_height()
        if not rpc_lowest_height:
            log.error(f"Failed to fetch lowest_height on {self.config.rpc}. Ensure the RPC URL format is correct and the node is online.")
            exit(5)
        self.rpc_lowest_height = int(rpc_lowest_height)
        
        if rpc_lowest_height != 1:
            log.warning(f"Provided API node is pruned. Check {self.config.api}/block?height=1. Ignoring.")

        log.info(f"""
---------------------RPC STATUS----------------------
URL: {self.config.rpc}
CHAIN_ID: {chain_id}
CATCHING_UP: {catching_up}
LATEST BLOCK: {latest_block_height} | {latest_block_time}
INDEXER: {tx_index.upper()}
LOWEST BLOCK: {rpc_lowest_height}
------------------------------------------------------
""")
        if chain_id != self.config.chain_id:
            log.error(f"Chain id missmatch. Expected {self.config.chain_id}, got {chain_id}")
            exit(5)

        if catching_up:
            log.warning(f"Provided RPC node is catching up. Check {self.rpc}/status. Ignoring.")

        if tx_index != 'on':
            log.warning(f"Provided RPC node is not indexing events. Ignoring.")
    
    # async def check_api_status(self):
        """Checks the RPC connection to ensure it is online."""
        result = await self.aio_session.get_api_status()
        if not result:
            log.error(f"Failed to connect to {self.config.rpc}. Ensure the RPC URL format is correct and the node is online.")
            exit(5)

        earliest_store_height = int(result['earliest_store_height'])
        latest_block_height = result['height']
        latest_block_time = result['timestamp']

        log.info(f"""
---------------------API STATUS----------------------
URL: {self.config.api}
LATEST BLOCK: {latest_block_height} | {latest_block_time}
EARLIEST BLOCK: {earliest_store_height}
------------------------------------------------------
""")
        if earliest_store_height != 0:
            log.warning(f"Provided API node is not archive. Check {self.config.api}/cosmos/base/node/v1beta1/status. Ignoring.")

    async def set_intial_all_vars(self):
        if self.config.end_height == 'auto':
            self.app_end_height = self.rpc_latest_height
            app_end_height_data = await self.aio_session.get_block(height=self.app_end_height)
            if app_end_height_data: 
                self.app_end_date = app_end_height_data['result']['signed_header']['header']['time'].split('T')[0]
            else:
                log.error(f"Failed to query app_end_height block: {self.app_end_height}")
                exit(5)
        else:
            self.app_end_height = self.config.end_height

        if self.config.start_height == 'auto':
            latest_processed_block = await self.mongo.get_latest_processed_block()
            if latest_processed_block['time'] is not None and latest_processed_block['height'] != 0:
                self.app_start_height = latest_processed_block['height'] + 1
            else:
                self.app_start_height = self.rpc_lowest_height
        else:
            self.app_start_height = self.config.start_height


        self.day_start_height = self.app_start_height

        app_start_block_data = await self.aio_session.get_block(height=self.app_start_height)
        if app_start_block_data:
            self.app_start_date = app_start_block_data['result']['signed_header']['header']['time'].split('T')[0]
            self.app_current_date = self.app_start_date
        else:
            log.error(f"Failed to query app_start_height block: {self.app_start_height}")
            exit(5)
        
        self.app_blocks_batch_size = self.config.blocks_batch_size
        self.app_sleep_between_blocks_batch = self.config.sleep_between_blocks_batch

        log.info(f"""
---------------------APP SETTINGS----------------------
START HEIGHT: {self.app_start_height}
START DATE: {self.app_start_date}
END HEIGHT: {self.app_end_height}
END DATE: {self.app_end_date}
BLOCKS BATCH SIZE: {self.app_blocks_batch_size}
------------------------------------------------------
""")
        
    async def start(self):
        await self.check_rpc_status()
        await self.set_intial_all_vars()
        # await self.get_validators()
        await self.parse_blocks_batches()

    async def get_validators(self):
        try:
            validators = []
            next_key = None

            async def fetch_with_retry(next_key):
                attempts = 0
                while attempts < 5:
                    try:
                        return await self.aio_session.get_validators(
                            status=None,
                            pagination_limit=100,
                            next_key=next_key
                        )
                    except Exception as e:
                        attempts += 1
                        log.warning(f"Retry {attempts}/5 after error: {e}")
                        await asyncio.sleep(5)
                raise Exception("Failed to fetch validators after 5 retries.")

            while True:
                page = await fetch_with_retry(next_key)
                validators.extend(page["validators"])
                next_key = page.get("pagination", {}).get("next_key")
                if not next_key:
                    break

            validators_result = {}
            if validators:
                for validator in validators:
                    _consensus_pub_key = validator["consensus_pubkey"]["key"]
                    _moniker = validator["description"]["moniker"]
                    _valoper = validator["operator_address"]
                    _hex = KeysUtils.pub_key_to_consensus_hex(pub_key=_consensus_pub_key)
                    _valcons = KeysUtils.pub_key_to_bech32(pub_key=_consensus_pub_key, address_refix="valcons")
                    _wallet = KeysUtils.valoper_to_account(valoper=_valoper)

                    validators_result[_hex] = {
                        "moniker": _moniker,
                        "hex": _hex,
                        "valoper": _valoper,
                        "consensus_pubkey": _consensus_pub_key,
                        "valcons": _valcons,
                        "wallet": _wallet
                    }
            # print(validators_result)
            return validators_result

        except Exception as e:
            log.error(f"An error occurred while fetching validators: {e}")

    async def get_block_signatures(self, height: int):
        
        async def fetch_with_retry(height, retries=3):
            for attempt in range(retries):
                try:
                    block = await self.aio_session.get_block(height=height)
                    if block and 'result' in block:
                        if attempt > 0:
                            log.info(f"Successfully fetched block {height} after {attempt + 1} attempt(s).")

                        return block
                    else:
                        raise ValueError("Invalid response")
                except Exception as e:
                    if attempt < retries - 1:
                        log.warning(f"Retrying block {height} request (attempt {attempt + 1}) due to: {e}")
                        await asyncio.sleep(3)
                    else:
                        log.error(f"Failed to fetch block {height} after {retries} attempt(s).")
                        return
        
        block = await fetch_with_retry(height=height)
        if block:

            signed_header = block['result']['signed_header']
            signatures = [
                signature['validator_address']
                for signature in signed_header['commit']['signatures']
            ]
            proposer = signed_header['header']['proposer_address']
            block_date = signed_header['header']['time'].split('T')[0]
            return {
                "height": height,
                "signatures": signatures,
                "proposer": proposer,
                "date": block_date
            }


    async def get_block_extension(self, height: int):
        
        async def fetch_with_retry(height, retries=3):
            for attempt in range(retries):
                try:
                    block = await self.aio_session.get_block_details(height=height)
                    if block and 'result' in block:
                        if attempt > 0:
                            log.info(f"Successfully fetched block {height} after {attempt + 1} attempt(s).")

                        return block
                    else:
                        raise ValueError("Invalid response")
                except Exception as e:
                    if attempt < retries - 1:
                        log.warning(f"Retrying block {height} request (attempt {attempt + 1}) due to: {e}")
                        await asyncio.sleep(3)
                    else:
                        log.error(f"Failed to fetch block {height} after {retries} attempt(s).")
                        return
        
        block = await fetch_with_retry(height=height)
        if block:
            block_txs = block['result']['block']['data']['txs']
            if block_txs:
                return block_txs[0]
            else:
                return ""

    async def get_all_valset(self, height: int):
        merged_valsets = []
        page = 1
        total = 0
        count = 0

        async def fetch_with_retry(height, page, retries=3):
            for attempt in range(retries):
                try:
                    sublist = await self.aio_session.get_valset_at_block(height=height, page=page)
                    if sublist and 'result' in sublist:
                        if attempt > 0:
                            log.info(f"Successfully fetched valset at height {height} & page {page} after {attempt + 1} attempt(s).")
                        return sublist
                    else:
                        raise ValueError("Invalid response")
                except Exception as e:
                    if attempt < retries - 1:
                        log.warning(f"Retrying valset request at height {height} / page {page} (attempt {attempt + 1}) due to: {e}")
                        await asyncio.sleep(3)
                    else:
                        log.error(f"Failed to fetch valset page {page} after {retries} attempt(s).")
                        return

        while count < total or total == 0:
            sublist = await fetch_with_retry(height, page)
            
            if not sublist:
                return

            validators = sublist['result']['validators']
            merged_valsets.extend(validator['address'] for validator in validators)
            count += int(sublist['result']['count'])
            total = int(sublist['result']['total'])
            page += 1

        return merged_valsets
    
    async def parse_blocks_batches(self):

        for height in range(self.app_start_height, self.app_end_height, self.app_blocks_batch_size):
            latest_height = min(height + self.app_blocks_batch_size, self.app_end_height)


            blocks_tasks = []
            valset_tasks = []
            extension_tasks = []

            for current_height in range(height, latest_height):
                blocks_tasks.append(self.get_block_signatures(height=current_height))
                valset_tasks.append(self.get_all_valset(height=current_height))
                extension_tasks.append(self.get_block_extension(height=current_height))

            blocks, valsets, extensions = await asyncio.gather(
                asyncio.gather(*blocks_tasks),
                asyncio.gather(*valset_tasks),
                asyncio.gather(*extension_tasks),
            )

            if self.config.multiprocessing:
                with Pool(os.cpu_count() - 1) as pool:
                    parsed_extensions = pool.map(process_extension, extensions)
            else:
                parsed_extensions = [process_extension(ext) for ext in extensions]

            for block, valset, parsed_extension in zip(blocks, valsets, parsed_extensions):
                if not block:
                    log.error(f"Failed to query {current_height-1} block\nMake sure block range {height} --> {latest_height} is available on the RPC\nOr try to reduce blocks_batch_size size in config\nExiting")
                    exit(5)

                if not valset:
                    log.error(f"Failed to query valset at block {current_height-1}\nMake sure block range {height} --> {latest_height} is available on the RPC\nOr try to reduce blocks_batch_size size in config\nExiting")
                    exit(5)

                if parsed_extension is None:
                    log.error(f"Failed to parse block extension at block {current_height-1}\nMake sure block range {height} --> {latest_height} is available on the RPC\nOr try to reduce blocks_batch_size size in config\nExiting")
                    exit(5)

                log.info(f"Block {block['height']} | Date {block['date']} | Valset {len(valset)} | Sigantures {len(block['signatures'])}")

                if self.app_current_date != block['date']:
                    log.info(f"Date changed: {self.app_current_date} -> {block['date']}. Inserting stats into DB")

                    await self.mongo.insert_daily_validator_stats(
                        date=self.app_current_date,
                        date_start_height=self.day_start_height,
                        date_end_height=self.app_current_height,
                        stats=self.validators
                    )

                    await self.mongo.update_latest_processed_block(
                        height=self.app_current_height,
                        time=self.app_current_date
                    )
                    self.validators.clear()
                    self.day_start_height = self.app_current_height + 1

                    if block['date'] == self.app_end_date:
                        log.info(f"End date reached: {block['date']}. Exiting")
                        return

                for hex in valset:
                    self.validators.setdefault(hex, {
                        'proposed_blocks': 0,
                        'signed_blocks': 0,
                        'missed_blocks': 0,
                        'signed_oracle': 0,
                        'missed_oracle': 0,
                    })

                    if hex == block['proposer']:
                        self.validators[hex]['proposed_blocks'] += 1

                    if hex in block['signatures']:
                        self.validators[hex]['signed_blocks'] += 1

                    else:
                        self.validators[hex]['missed_blocks'] += 1
                    
                    if parsed_extension.get(hex) is True:
                        self.validators[hex]['signed_oracle'] += 1
                    elif parsed_extension.get(hex) is False:
                        self.validators[hex]['missed_oracle'] += 1
                    else:
                        log.warning(f"Missing active validator in vote extension. Ignoring... {self.validators[hex]}: {parsed_extension}")

                self.app_current_date = block['date']
                self.app_current_height = block['height']

            if self.app_sleep_between_blocks_batch:
                await asyncio.sleep(self.app_sleep_between_blocks_batch)


def process_extension(tx: str):
    extension_validators = ExtensionParser.parse_votes_extension(tx=tx)
    return {
        KeysUtils.consensus_pubkey_bytes_to_hex(v['validator_address']): bool(v['pairs'])
        for v in extension_validators
    }
    
def load_config(path: str) -> Config:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return Config(**data)

async def main():
    config_path = args.config or "config.yaml"
    log.info(f"Loading config from {args.config}")
    config = load_config(path=config_path)

    log.info(f"Setting default_bech32_prefix for KeysUtils to {config.bech_32_prefix}")
    KeysUtils.default_bech32_prefix = config.bech_32_prefix
    
    async with MongoDBHandler(config) as mongo, AioHttpCalls(api=config.api, rpc=config.rpc) as aio_session:

        app = App(config=config, aio_session=aio_session, mongo=mongo)
        await app.start()
          
if __name__ == "__main__":
    asyncio.run(main())
