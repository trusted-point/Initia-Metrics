import asyncio
from typing import Literal
from sys import exit
from json import loads

from utils.config import Config
from utils.logger import log

from src.aio_calls import AioHttpCalls
from src.decoder import KeysUtils
from src.mongodb import MongoDBHandler

class Metrics:
    def __init__(
        self,
        config: Config,
        aio_session: AioHttpCalls,
        mongo: MongoDBHandler,
        metric: Literal['gov', 'slash']
    ):
        self.aio_session = aio_session
        self.mongo = mongo
        self.config = config
        self.metrics_batch_size = config.metrics_batch_size
        self.metric = metric

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

        rpc_lowest_height = await self.aio_session.get_rpc_lowest_height()
        if not rpc_lowest_height:
            log.error(f"Failed to fetch lowest_height on {self.config.rpc}. Ensure the RPC URL format is correct and the node is online.")
            exit(5)
        
        if rpc_lowest_height != 1:
            log.warning(f"Provided API node is pruned. Check {self.config.api}/block?height=1. Ignoring...")
            await asyncio.sleep(5)

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
            log.warning(f"Provided RPC node is not indexing events. Ignoring...")
            await asyncio.sleep(5)

    async def check_api_status(self):
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

    async def get_validators(self):
        validators = []
        next_key = None

        async def fetch_with_retry(next_key, retries=3):
            for attempt in range(retries):
                try:
                    result = await self.aio_session.fetch_validators(
                        status=None,
                        pagination_limit=100,
                        next_key=next_key
                    )
                    if result and 'validators' in result:
                        if attempt > 0:
                            log.info(f"Successfully fetched {len(result['validators'])} validators after {attempt + 1} attempt(s).")
                        return result
                    else:
                        raise ValueError("Invalid response")
                    
                except Exception as e:
                    if attempt < retries - 1:
                        log.warning(f"Retrying block validators request (attempt {attempt + 1}) due to: {e}")
                        await asyncio.sleep(3)
                    else:
                        log.error(f"Failed to fetch validators after {retries} attempt(s).")
                        return

        while True:
            page = await fetch_with_retry(next_key)
            if not page:
                exit(5)
            validators.extend(page["validators"])
            next_key = page.get("pagination", {}).get("next_key")
            if not next_key:
                break

        validators_result = []
        if validators:
            for validator in validators:
                _consensus_pub_key = validator["consensus_pubkey"]["key"]
                _moniker = validator["description"]["moniker"]
                _valoper = validator["operator_address"]
                _hex = KeysUtils.pub_key_to_consensus_hex(pub_key=_consensus_pub_key)
                _valcons = KeysUtils.pub_key_to_bech32(pub_key=_consensus_pub_key, address_refix="valcons")
                _wallet = KeysUtils.valoper_to_account(valoper=_valoper)

                validators_result.append({
                    "moniker": _moniker,
                    "hex": _hex,
                    "valoper": _valoper,
                    "consensus_pubkey": _consensus_pub_key,
                    "valcons": _valcons,
                    "wallet": _wallet
                })
        log.info(f"Succesfully fecthed {len(validators_result)} validators")
        return validators_result

    async def get_proposals(self):
        proposals = []
        next_key = None

        async def fetch_with_retry(next_key, retries=3):
            for attempt in range(retries):
                try:
                    result = await self.aio_session.fetch_proposals(
                        status=None,
                        pagination_limit=100,
                        next_key=next_key
                    )
                    if result and 'proposals' in result:
                        if attempt > 0:
                            log.info(f"Successfully fetched {len(result['proposals'])} proposals after {attempt + 1} attempt(s).")
                        return result
                    else:
                        raise ValueError("Invalid response")
                    
                except Exception as e:
                    if attempt < retries - 1:
                        log.warning(f"Retrying block proposals request (attempt {attempt + 1}) due to: {e}")
                        await asyncio.sleep(3)
                    else:
                        log.error(f"Failed to fetch proposals after {retries} attempt(s).")
                        return

        while True:
            page = await fetch_with_retry(next_key)
            if not page:
                exit(5)
            proposals.extend(page["proposals"])
            next_key = page.get("pagination", {}).get("next_key")
            if not next_key:
                break

        log.info(f"Succesfully fecthed {len(proposals)} proposals")
        return proposals
    
    async def update_slashes(self):
        validators = await self.get_validators()
        for validator in validators:
            valoper = validator['valoper']
            data = await self.aio_session.get_slashing_events(valcons=validator['valcons'])
            if data is not None:
                if len(data['result']['blocks']) > 0:
                    for block in data['result']['blocks']:
                        height = int(block['block']['header']['height'])
                        date = block['block']['header']['time']
                        log.info(f"Found slash for {validator['moniker']} [{valoper}]: {height} {date}")
                        await self.mongo.add_validator_slash(date=date, height=height, valoper=valoper)
                else:
                    log.info(f"0 slashes for {validator['moniker']} [{valoper}]")
            else:
                log.error(f"Failed to fetch slashes for {validator['moniker']} [{valoper}]")

    async def update_governance(self):

        vote_options = {
            0: "Unspecified", # VOTE_OPTION_UNSPECIFIED
            1: "Yes",         # VOTE_OPTION_YES
            2: "Abstain",     # VOTE_OPTION_ABSTAIN
            3: "No",          # VOTE_OPTION_NO
            4: "NoWithVeto",  # VOTE_OPTION_NO_WITH_VETO
        }

        validators = await self.get_validators()
        proposals = await self.get_proposals()
        processed_proposals = await self.mongo.get_processed_proposals()

        if processed_proposals == []:
            log.warning(f"0 processed proposals found in DB")
        processed_proposal_ids = []
        for prop in processed_proposals:
            processed_proposal_ids.append(prop['_id'])

        allowed_prop_status = ["PROPOSAL_STATUS_PASSED","PROPOSAL_STATUS_REJECTED", "PROPOSAL_STATUS_FAILED"]

        for proposal in proposals:
            status = proposal['status']
            id = proposal['id']
            valdiators_votes = {}
            if status in allowed_prop_status and id not in processed_proposal_ids:
                log.info(f"Processing proposal {id} & {status}")
                await self.mongo.inserts_proposal(proposal_id=id)
                for validator in validators:
                    valoper = validator['valoper']
                    wallet = validator['wallet']
                    proposal_vote = await self.aio_session.get_gov_vote_tx(wallet=wallet, proposal_id=id)
                    if proposal_vote is not None:
                        if proposal_vote['result']['txs']:
                            valid_txs = [
                                tx for tx in proposal_vote['result']['txs']
                                if tx["tx_result"]["code"] == 0
                            ]
                            if valid_txs:
                                last_tx = max(valid_txs, key=lambda tx: int(tx["height"]))
                                tx_hash = last_tx["hash"]
                                tx_height = int(last_tx["height"])
                                for event in last_tx["tx_result"]["events"]:
                                    event_type = event["type"]
                                    if event_type == "proposal_vote":
                                        attrs = {a["key"]: a["value"] for a in event["attributes"]}
                                        option_data = loads(attrs["option"])
                                        option = vote_options[option_data[0]["option"]]
                                        valdiators_votes[valoper] = {"height": tx_height, "option": option, "hash": tx_hash}
                                        log.info(f"{id}: {option} - {valoper} (tx {tx_hash} @ {tx_height})")
                                        await self.mongo.update_validator_vote(proposal_id=id, valoper=valoper, option=option, tx_height=tx_height, tx_hash=tx_hash)
                            else:
                                log.warning(f"Valid gov TXs for {id} from {wallet} not found")
                        else:
                            log.warning(f"Gov TXs for {id} from {wallet} not found")
                    else:
                        log.error(f"Failed to fetch gov vote for {id} {wallet}")
                        exit(5)


    async def start(self):
        await self.check_rpc_status()
        await self.check_api_status()

        if self.metric == "slash":
            await self.update_slashes()
        elif self.metric == "gov":
            await self.update_governance()


