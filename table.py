import unicodedata
from json import load
from tabulate import tabulate
from emoji import demojize

def format_moniker(moniker: str, max_length: int=30):
    try:
        moniker = ''.join([c for c in unicodedata.normalize('NFKD', demojize(moniker)) if not unicodedata.combining(c)])
        moniker = ''.join(c for c in moniker if c.isalnum() or c.isspace() or c == '_' or c == '-' or c == '.').replace('ꝏ', ' ').strip()[:max_length]
        return moniker
    except Exception:
        return moniker
        
with open('metrics.json', 'r') as f:
    data = load(f)

sorted_data = sorted(data['validators'], key=lambda x: x['total_signed_blocks'], reverse=True)

headers = ["#","Moniker", "Total Signed Blocks", "Total Missed Blocks", "Total Oracle Votes", "Total Missed Oracle Votes", "Jails Number", "Voted Proposals"]

rows = []
for index, validator in enumerate(sorted_data, start=1):
    moniker = format_moniker(validator['moniker'])
    total_signed_blocks = validator.get('total_signed_blocks', 0)
    total_missed_blocks = validator.get('total_missed_blocks', 0)
    total_oracle_votes = validator.get('total_oracle_votes', 0)
    total_missed_oracle_votes = validator.get('total_missed_oracle_votes', 0)
    slashing_info_length = len(validator.get('slashing_info', [])) if validator.get('slashing_info') is not None else 0
    gov_info_length = len(validator.get('governance', {})) if validator.get('slashing_info') is not None else 0

    rows.append([
        index,
        moniker,
        total_signed_blocks,
        total_missed_blocks,
        total_oracle_votes,
        total_missed_oracle_votes,
        slashing_info_length,
        gov_info_length
    ])

print(tabulate(rows, headers=headers, tablefmt="grid"))
