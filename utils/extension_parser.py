import base64
import zstd
import zlib
import sys
import os

proto_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'proto'))
sys.path.append(proto_dir)

from utils.proto.types_pb2 import ExtendedCommitInfo
from utils.proto.slinky.abci.v1.vote_extensions_pb2 import OracleVoteExtension

class ExtensionParser:
    def __init__(self, logger):
        self.logger = logger

    def parse_votes_extension(self, tx: str):
        try:
            result = []
            compressed_data = base64.b64decode(tx)
            decompressed_data = zstd.decompress(compressed_data)
            extended_commit_info = ExtendedCommitInfo()
            extended_commit_info.ParseFromString(decompressed_data)
            for vote in extended_commit_info.votes:
                if vote:
                    inner_result = {'validator_address': vote.validator.address, 'pairs' : []}
                    if vote.vote_extension:
                        vote_extension_data = zlib.decompress(vote.vote_extension)
                        vote_extension_info = OracleVoteExtension()
                        vote_extension_info.ParseFromString(vote_extension_data)
                        for price_id, price_bz in vote_extension_info.prices.items():
                            price = int.from_bytes(price_bz, byteorder='big', signed=False)
                            inner_result['pairs'].append({'pair': price_id, 'price': price})
                    result.append(inner_result)
            return result
        
        except zlib.error as e:
            self.logger.error(f"Zlib error processing vote: {e}")
        except zstd.Error as e:
            self.logger.error(f"Zstd decompress error: {e}")
        except Exception as e:
            self.logger.error(f"Error processing vote: {e}")