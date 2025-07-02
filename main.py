import yaml
import asyncio
from sys import exit

from utils.args import args
from utils.logger import log
from utils.config import Config

from src.aio_calls import AioHttpCalls
from src.decoder import KeysUtils
from src.mongodb import MongoDBHandler
from src.blocks import Blocks
from src.metrics import Metrics
from src.excel import Excel

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
    
    async with MongoDBHandler(config) as mongo, \
               AioHttpCalls(api=config.api, rpc=config.rpc) as aio_session:
        if args.subcommand == "blocks":
            app = Blocks(config=config, aio_session=aio_session, mongo=mongo)
        elif args.subcommand == "metrics":
            app = Metrics(config=config, aio_session=aio_session, mongo=mongo, metric=args.metric)
        elif args.subcommand == "excel":
            app = Excel(aio_session=aio_session, mongo=mongo, excel_sheet_name=args.sheet, excel_file_name=args.file)

        else:
            exit(1)
        await app.start()


if __name__ == "__main__":
    asyncio.run(main())
