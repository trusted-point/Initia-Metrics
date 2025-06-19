from pydantic import BaseModel

class DB(BaseModel):
    username: str
    password: str
    ip: str
    port: int
    db_name: str

class Config(BaseModel):
    rpc: str
    api: str
    bech_32_prefix: str
    chain_id: str
    blocks_batch_size: int
    sleep_between_blocks_batch: int
    metrics_batch_size: int
    multiprocessing: bool
    start_height: int | str
    end_height: int | str
    db: DB