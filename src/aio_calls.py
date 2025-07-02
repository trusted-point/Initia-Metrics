import aiohttp
import traceback
from utils.logger import log
from urllib.parse import quote
from typing import Literal, Optional
class AioHttpCalls:

    def __init__(
                 self,
                 api,
                 rpc,
                 timeout = 10
                 ):
                 
        self.api = api
        self.rpc = rpc
        self.timeout = timeout
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        log.info("✅ Created AioHttp session")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        log.info("🛑 AioHttp connection closed.")
        await self.session.close()
    
    async def handle_request(self, url, callback,):
        try:
            log.debug(f"Requesting {url}")
            async with self.session.get(url, timeout=self.timeout) as response:
                
                if 200 <= response.status < 300:
                    return await callback(response.json())
                elif response.status == 500 and '/block?height=1' in url:
                    return await callback(response.json())
                else:
                    log.debug(f"Request to {url} failed with status code {response.status}")
                
        except aiohttp.ClientError as e:
            log.debug(f"Issue with making request to {url}: {e}")
        
        except TimeoutError as e:
            log.debug(f"Issue with making request to {url}. TimeoutError: {e}")

        except Exception as e:
            log.debug(f"An unexpected error occurred: {e}")
            traceback.print_exc()
    

    async def get_rpc_status(self):
        url = f"{self.rpc}/status"

        async def process_response(response):
            data = await response
            return data["result"]

        return await self.handle_request(url, process_response)

    async def get_api_status(self):
        url = f"{self.api}/cosmos/base/node/v1beta1/status"

        async def process_response(response):
            data = await response
            return data

        return await self.handle_request(url, process_response)
    
    async def get_total_delegators(self, valoper: str) -> str:
        url = f"{self.api}/initia/mstaking/v1/validators/{valoper}/delegations?pagination.count_total=true"
        
        async def process_response(response):
            data = await response
            return int(data.get('pagination', {}).get('total', 0))
        
        return await self.handle_request(url, process_response)
    
    async def get_validator_tomb(self, valcons: str) -> dict:
        url = f"{self.api}/cosmos/slashing/v1beta1/signing_infos/{valcons}"

        async def process_response(response):
            data = await response
            return data.get('val_signing_info',{}).get('tombstoned', False)

        return await self.handle_request(url, process_response)
    
    async def get_validator_creation_block(self, valoper: str) -> dict:
        url=f"{self.rpc}/tx_search?query=%22create_validator.validator=%27{valoper}%27%22"

        async def process_response(response):
            data = await response
            if data:
                for transaction in data['result']['txs']:
                    if transaction.get('tx_result',{}).get('code') == 0:
                        return {'tx_hash': transaction.get('hash'),'height': transaction.get('height')}

        return await self.handle_request(url, process_response)

    async def get_gov_vote_tx(self, wallet: str, proposal_id: int) -> dict:
        # url=f"{self.rpc}/tx_search?query=%22proposal_vote.voter=%27{wallet}%27%22"

        url=f"{self.rpc}/tx_search?query=%22proposal_vote.voter=%27{wallet}%27 AND proposal_vote.proposal_id=%27{proposal_id}%27%22"
        
        async def process_response(response):
            data = await response

            # voted_proposals = {}
            # if data.get('result',{}).get('txs', []):
            #     for tx in data["result"]["txs"]:
            #         if tx["tx_result"]["code"] == 0:
            #             tx_hash = tx["hash"]
            #             for event in tx["tx_result"]["events"]:
            #                 if event["type"] == "proposal_vote":
            #                     attributes = {attr["key"]: attr["value"] for attr in event["attributes"]}
            #                     proposal_id = int(attributes["proposal_id"])
            #                     option_data = loads(attributes["option"])
            #                     option = option_data[0]["option"]
            #                     if proposal_id not in voted_proposals:
            #                         voted_proposals[proposal_id] = {
            #                             "option": option,
            #                             "tx_hash": tx_hash
            #                         }
            return data
        return await self.handle_request(url, process_response)
    

    async def fetch_proposals(
        self,
        status: Optional[
            Literal[
                "PROPOSAL_STATUS_UNSPECIFIED",
                "PROPOSAL_STATUS_DEPOSIT_PERIOD",
                "PROPOSAL_STATUS_PASSED",
                "PROPOSAL_STATUS_REJECTED",
                "PROPOSAL_STATUS_FAILED"
            ]
        ] = None,        
        pagination_limit: int = 100,
        next_key: Optional[str] = None,
    ) -> dict:

        url = f"{self.api}/initia/gov/v1/proposals?pagination.limit={pagination_limit}"

        if status:
            url += f"&proposal_status={quote(status)}"
        if next_key:
            url += f"&pagination.key={quote(next_key)}"
            
        async def process_response(response):
            data = await response
            return data
        
        return await self.handle_request(url, process_response)

    async def fetch_validators(
        self,
        status: Optional[
            Literal[
                "BOND_STATUS_BONDED",
                "BOND_STATUS_UNBONDED",
                "BOND_STATUS_UNBONDING",
            ]
        ] = None,
        pagination_limit: int = 100,
        next_key: Optional[str] = None,
    ) -> dict:
        url = f"{self.api}/initia/mstaking/v1/validators?pagination.limit={pagination_limit}"

        if status:
            url += f"&status={quote(status)}"
        if next_key:
            url += f"&pagination.key={quote(next_key)}"

        async def process_response(response):
            return await response 

        return await self.handle_request(url, process_response)

    async def get_slashing_events(self, valcons: str) -> dict:
        url = f'{self.rpc}/block_search?query="slash.address%3D%27{valcons}%27"'

        async def process_response(response):
            data = await response
            return data
            
        return await self.handle_request(url, process_response)
    
    async def get_valset_at_block(self, height):
        url = f"{self.api}/cosmos/base/tendermint/v1beta1/validatorsets/{height}?&pagination.limit=100000"
        
        async def process_response(response):
            data = await response
            valcons = []
            for validator in data['validators']:
                valcons.append(validator['address'])
            return {'height': height, 'vaset': valcons}
        
        return await self.handle_request(url, process_response)
    
    async def get_block(self, height):
        url = f"{self.rpc}/commit?height={height}"

        async def process_response(response):
            data = await response
            return data
        return await self.handle_request(url, process_response)

    async def get_valset_at_block(self, height, page):
        url = f"{self.rpc}/validators?height={height}&page={page}&per_page=100"

        async def process_response(response):
            data = await response
            return data
        
        return await self.handle_request(url, process_response)

    async def get_block_details(self, height):
        url = f"{self.rpc}/block?height={height}"
        
        async def process_response(response):
            data = await response
            return data
        
        return await self.handle_request(url, process_response)
    
    async def get_rpc_lowest_height(self):
        url = f"{self.rpc}/block?height=1"

        async def process_response(response):
            data = await response

            error_data = data.get('error')
            if error_data:
                error_message = error_data.get('data')
                if error_message:
                    return int(error_message.split()[-1])
            
            return int(data.get('result', {}).get('block', {}).get('header', {}).get('height'))
                
        return await self.handle_request(url, process_response)