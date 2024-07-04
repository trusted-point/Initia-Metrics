from json import load, dump
from yaml import safe_load

with open('metrics.json', 'r') as file:
    metrics_data = load(file)

with open('config.yaml', 'r') as config_file:
    config = safe_load(config_file)

for validator in metrics_data['validators']:
    validator['total_signed_blocks'] = 0
    validator['total_missed_blocks'] = 0
    validator['total_proposed_blocks'] = 0
    validator['total_oracle_votes'] = 0
    validator['total_missed_oracle_votes'] = 0

metrics_data['latest_height'] = config['start_height']

with open('metrics.json', 'w') as file:
    dump(metrics_data, file)