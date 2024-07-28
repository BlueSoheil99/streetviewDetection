import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)


def get_config(attributes:list):
    return [config[attribute] for attribute in attributes]
