import asyncio
from json import load, dump
from yaml import safe_load
from utils.logger import log
from utils.args import args

# from src.aio_calls import AioHttpCalls


# from src.decoder import Decoder
from src.extension import ExtensionParser
# from multiprocessing import Pool




print(args)


# with open(ar, 'r') as config_file:
#     config = safe_load(config_file)


# logger = setup_logger(log_level=config['log_lvl'])

# decoder = Decoder(bech32_prefix=config['bech_32_prefix'], logger=logger)

# extension_parser = ExtensionParser(logger=logger)

# async def get_validators(session: AioHttpCalls):
#     validators = await session.get_validators(status=None)
#     if validators:
#         filtered_valdiators = []
#         for validator in validators:
#             validator['wallet'] = decoder.convert_valoper_to_account(valoper=validator['valoper'])
#             validator['valcons'] = decoder.convert_consenses_pubkey_to_valcons(consensus_pub_key=validator['consensus_pubkey'])
#             validator['hex'] = decoder.conver_valcons_to_hex(valcons=validator['valcons'])
#             validator['total_signed_blocks'] = 0
#             validator['total_missed_blocks'] = 0
#             validator['total_proposed_blocks'] = 0
#             validator['total_oracle_votes'] = 0
#             validator['total_missed_oracle_votes'] = 0
#             filtered_valdiators.append(validator)
#         return filtered_valdiators

# async def get_slashing_info(validators, session, start_height, end_height):
#     task = [session.get_slashing_info_archive(validator['valcons'], start_height=start_height, end_height=end_height) for validator in validators]
#     results = await asyncio.gather(*task)
#     for validator, result in zip(validators, results):
#         validator['slashing_info'] = result
#     return validators

# async def get_delegators_number(validators, session):
#     task = [session.get_total_delegators(validator['valoper']) for validator in validators]
#     results = await asyncio.gather(*task)
#     for validator, result in zip(validators, results):
#         validator['delegators_count'] = result
#     return validators

# async def get_validator_creation_info(validators, session):
#     task = [session.get_validator_creation_block(validator['valoper']) for validator in validators]
#     results = await asyncio.gather(*task)
#     for validator, result in zip(validators, results):
#         validator['validator_creation_info'] = result
#     return validators

# async def check_valdiator_tomb(validators, session):
#     task = [session.get_validator_tomb(validator['valcons']) for validator in validators]
#     results = await asyncio.gather(*task)
#     for validator, result in zip(validators, results):
#         validator['tombstoned'] = result if result is not None else False
#     return validators

# async def fetch_governance_transactions(validators, session):
#     task = [session.get_gov_votes(validator['wallet']) for validator in validators]
#     results = await asyncio.gather(*task)
#     for validator, result in zip(validators, results):
#         validator['governance'] = result
#     return validators

# # IN CASE THERE ARE MORE THAN 100 VALS IN THE SET
# async def get_all_valset(session, height, max_vals):
#     valset_tasks = []
#     if max_vals <= 100:
#         page_max = 1
#     elif 100 < max_vals <= 200:
#         page_max = 2
#     elif 200 < max_vals <= 300:
#         page_max = 3
#     else:
#         page_max = 4

#     for page in range(1, page_max + 1):
#         valset_tasks.append(session.get_valset_at_block_hex(height=height, page=page))
#     valset = await asyncio.gather(*valset_tasks)
    
#     merged_valsets = []

#     for sublist in valset:
#         if sublist is not None:
#             for itm in  sublist:
#                 merged_valsets.append(itm)

#     return merged_valsets

# def process_extension(tx: str):
#     try:
#         extension_validators = extension_parser.parse_votes_extension(tx=tx)
#         data = {}
#         for validator in extension_validators:
#             valcons = decoder.convert_consenses_pubkey_to_valcons(address_bytes=validator['validator_address'])
#             data[valcons] = 1 if validator['pairs'] else 0
#         return data
#     except Exception as e:
#         logger.error(f"Failed to process block extension. An unexpected error occurred: {e}")

# async def parse_signatures_batches(validators, session: AioHttpCalls, start_height, end_height, metrics_file_name, batch_size):

#     with tqdm(total=end_height, desc="Parsing Blocks", unit="block", initial=start_height) as pbar:

#         for height in range(start_height, end_height, batch_size):
#             inner_end_height = min(height + batch_size, end_height)
#             max_vals = config.get('max_number_of_valdiators_ever_in_the_active_set') or 125

#             signature_tasks = []
#             valset_tasks = []
#             tx_tasks = []
            
#             for current_height in range(height, inner_end_height):
#                 signature_tasks.append(session.get_block_signatures(height=current_height))
#                 if max_vals > 100:
#                     valset_tasks.append(get_all_valset(session=session, height=current_height, max_vals=max_vals))
#                 else:
#                     valset_tasks.append(session.get_valset_at_block_hex(height=current_height, page=1))
#                 tx_tasks.append(session.get_extension_tx(height=current_height)) 
            
#             blocks, valsets, txs = await asyncio.gather(
#                 asyncio.gather(*signature_tasks),
#                 asyncio.gather(*valset_tasks),
#                 asyncio.gather(*tx_tasks)
#             )

#             if config['multiprocessing']:
#                 try:
#                     with Pool(os.cpu_count() - 1) as pool:
#                         parsed_extensions = pool.map(process_extension, txs)
#                 except (Exception, KeyboardInterrupt) as e:
#                     logger.error(f"Failed to process block extension. Exiting: {e}")
#                     pool.close()
#                     exit(1)
#             else:
#                 parsed_extensions = []
#                 for tx in txs:
#                     parsed_extensions.append(process_extension(tx))

#             for block, valset, extension in zip(blocks, valsets, parsed_extensions):
#                 if block is None or valset is None or not extension:
#                     logger.error("Failed to fetch block/valset info. Try to reduce batch size or increase start_height in config.yaml and restart. Exiting")
#                     exit(1)

#                 for validator in validators:
#                     if validator['hex'] in valset:
#                         if validator['hex'] == block['proposer']:
#                             validator['total_proposed_blocks'] += 1
#                         if validator['hex'] in block['signatures']:
#                             validator['total_signed_blocks'] += 1
#                         else:
#                             validator['total_missed_blocks'] += 1
#                         if extension.get(validator['valcons']):
#                             validator['total_oracle_votes'] += 1
#                         else:
#                             validator['total_missed_oracle_votes'] += 1

#             metrics_data = {
#                 'latest_height': inner_end_height,
#                 'validators': validators
#             }
#             with open(metrics_file_name, 'w') as file:
#                 dump(metrics_data, file)
            
#             pbar.update(inner_end_height - height)

# async def main():
#     async with AioHttpCalls(config=config, logger=logger, timeout=800) as session:
#         rpc_latest_height = await session.get_latest_block_height_rpc()
#         if not rpc_latest_height:
#             logger.error("Failed to fetch RPC latest height. RPC is not reachable. Exiting.")
#             exit(1)
#         end_height = config.get('end_height')
#         if end_height:
#             if end_height > int(rpc_latest_height):
#                 end_height = int(rpc_latest_height)
#                 logger.error(f"Config end_height [{config.get('end_height')}] > Latest height available on the RPC [{rpc_latest_height}]. Setting end_height: {end_height}")
#         else:
#             end_height = int(rpc_latest_height)
#             logger.error(f"end_height not provided in config.yaml. Setting end height: {end_height}")

#         if not os.path.exists(config.get('metrics_file_name','metrics.json')):
#             if not config.get('start_height'):
#                 logger.info(f'Start height not provided. Trying to fetch lowest height on the RPC')

#             start_height = config.get('start_height', 1)
#             rpc_lowest_height = await session.fetch_lowest_height()

#             if rpc_lowest_height:
#                 if rpc_lowest_height > start_height:
#                     start_height = rpc_lowest_height
#                     print('------------------------------------------------------------------------')
#                     logger.error(f"Config or default start height [{config.get('start_height', 1)}] < Lowest height available on the RPC [{rpc_lowest_height}]")
#             else:
#                 logger.error(f'Failed to get lowest height available on the RPC')
#                 exit(1)

#             print('------------------------------------------------------------------------')
#             logger.info('Fetching latest validators set')
#             validators = await get_validators(session=session)
#             if not validators:
#                 logger.error("Failed to fetch validators. API is not reachable. Exiting")
#                 exit(1)
#             if config['metrics']['validator_creation_block']:
#                 print('------------------------------------------------------------------------')
#                 logger.info('Fetching validator creation info')
#                 validators = await get_validator_creation_info(validators=validators, session=session)
#             if config['metrics']['jails_info']:
#                 print('------------------------------------------------------------------------')
#                 logger.info('Fetching slashing info')
#                 validators = await get_slashing_info(validators=validators, session=session, start_height=start_height, end_height=end_height)
#             if config['metrics']['governance_participation']:
#                 print('------------------------------------------------------------------------')
#                 logger.info('Fetching governance participation')
#                 validators = await fetch_governance_transactions(validators=validators, session=session)
#             if config['metrics']['delegators']:
#                 print('------------------------------------------------------------------------')
#                 logger.info('Fetching delegators info')
#                 validators = await get_delegators_number(validators=validators, session=session)

#             print('------------------------------------------------------------------------')
#             logger.info('Fetching tombstones info')
#             validators = await check_valdiator_tomb(validators=validators, session=session)
#             print('------------------------------------------------------------------------')

#             logger.info(f'Indexing blocks from the height: {start_height}')
#             print('------------------------------------------------------------------------')

#             await parse_signatures_batches(validators=validators, session=session, start_height=start_height, end_height=end_height, batch_size=config['batch_size'], metrics_file_name=config.get('metrics_file_name','metrics.json'))
#         else:
#             with open(config.get('metrics_file_name','metrics.json'), 'r') as file:
#                 metrics_data = load(file)
#                 print('------------------------------------------------------------------------')
#                 logger.info(f"Continue indexing blocks from {metrics_data.get('latest_height', 1)}")
#                 await parse_signatures_batches(validators=metrics_data['validators'], session=session, start_height=metrics_data['latest_height'], end_height=end_height, batch_size=config['batch_size'], metrics_file_name=config.get('metrics_file_name','metrics.json'))

# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print('\n------------------------------------------------------------------------')
#         logger.info("The script was stopped")
#         print('------------------------------------------------------------------------\n')
#         exit(0)
