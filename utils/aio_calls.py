import aiohttp
import traceback
from json import loads

class AioHttpCalls:

    def __init__(
                 self,
                 config,
                 logger,
                 timeout = 10
                 ):
                 
        self.api = config['api']
        self.rpc = config['rpc']
        self.logger = logger
        self.timeout = timeout
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.session.close()
    
    async def handle_request(self, url, callback,):
        try:
            async with self.session.get(url, timeout=self.timeout) as response:
                
                if 200 <= response.status < 300:
                    return await callback(response.json())
                elif response.status == 500 and '/block?height=1' in url:
                    return await callback(response.json())
                else:
                    self.logger.debug(f"Request to {url} failed with status code {response.status}")
                
        except aiohttp.ClientError as e:
            self.logger.debug(f"Issue with making request to {url}: {e}")
        
        except TimeoutError as e:
            self.logger.debug(f"Issue with making request to {url}. TimeoutError: {e}")

        except Exception as e:
            self.logger.debug(f"An unexpected error occurred: {e}")
            traceback.print_exc()
    
    async def get_latest_block_height_rpc(self) -> str:
        url = f"{self.rpc}/abci_info"

        async def process_response(response):
            data = await response
            return int(data.get('result', {}).get('response', {}).get('last_block_height'))
        
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

    async def get_gov_votes(self, wallet: str) -> dict:
        url=f"{self.rpc}/tx_search?query=%22proposal_vote.voter=%27{wallet}%27%22"
        
        async def process_response(response):
            data = await response

            voted_proposals = {}
            if data.get('result',{}).get('txs', []):
                for tx in data["result"]["txs"]:
                    if tx["tx_result"]["code"] == 0:
                        tx_hash = tx["hash"]
                        for event in tx["tx_result"]["events"]:
                            if event["type"] == "proposal_vote":
                                attributes = {attr["key"]: attr["value"] for attr in event["attributes"]}
                                proposal_id = int(attributes["proposal_id"])
                                option_data = loads(attributes["option"])
                                option = option_data[0]["option"]
                                if proposal_id not in voted_proposals:
                                    voted_proposals[proposal_id] = {
                                        "option": option,
                                        "tx_hash": tx_hash
                                    }
            return voted_proposals
        return await self.handle_request(url, process_response)

    async def get_validators(self, status: str = None) -> list:
        status_urls = {
            "BOND_STATUS_BONDED": f"{self.api}/initia/mstaking/v1/validators?status=BOND_STATUS_BONDED&pagination.limit=100000",
            "BOND_STATUS_UNBONDED": f"{self.api}/initia/mstaking/v1/validators?status=BOND_STATUS_UNBONDED&pagination.limit=100000",
            "BOND_STATUS_UNBONDING": f"{self.api}/initia/mstaking/v1/validators?status=BOND_STATUS_UNBONDING&pagination.limit=100000",
            None: f"{self.api}/initia/mstaking/v1/validators?&pagination.limit=100000"
        }
        url = status_urls.get(status, status_urls[None])
        async def process_response(response):
            data = await response
            validators = []
            for validator in data['validators']:
                info = {'moniker': validator.get('description',{}).get('moniker'),
                        'valoper': validator.get('operator_address'),
                        'consensus_pubkey': validator.get('consensus_pubkey',{}).get('key')}
                validators.append(info)
            return validators
        
        return await self.handle_request(url, process_response)
    
    async def get_slashing_info_archive(self, valcons: str, start_height, end_height):
        url = f'{self.rpc}/block_search?query="slash.address%3D%27{valcons}%27"'
        
        async def process_response(response):
            blocks = []
            data = await response
            if data.get('result',{}).get('blocks'):
                for block in data['result']['blocks']:
                    height = int(block.get('block',{}).get('header',{}).get('height', 1))
                    if height in range(start_height, end_height+1):
                        blocks.append({'height': height, 'time': block.get('block',{}).get('header',{}).get('time')})
                return blocks
            
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
    
    async def get_block_signatures(self, height):
        url = f"{self.rpc}/commit?height={height}"

        async def process_response(response):
            data = await response
            signatures = []
        
            for signature in data['result']['signed_header']['commit']['signatures']:
                signatures.append(signature['validator_address'])
            proposer = data['result']['signed_header']['header']['proposer_address']
            
            return {'height': height, 'signatures': signatures, 'proposer': proposer}

        return await self.handle_request(url, process_response)

    async def get_valset_at_block_hex(self, height, page):
        url = f"{self.rpc}/validators?height={height}&page={page}&per_page=100"
        
        async def process_response(response):
            data = await response
            valset_hex = []
            for validator in data['result']['validators']:
                valset_hex.append(validator['address'])

            return valset_hex
        
        return await self.handle_request(url, process_response)

    async def get_extension_tx(self, height):
        url = f"{self.rpc}/block?height={height}"
        
        async def process_response(response):
            data = await response
            return data['result']['block']['data']['txs'][0]
        
        return await self.handle_request(url, process_response)
    
    async def fetch_lowest_height(self):
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