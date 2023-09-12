from dotenv import load_dotenv
import os
import requests
from web3 import Web3


load_dotenv()
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ALCHEMY_API_KEY = os.environ['ALCHEMY_API_KEY']
APIS = {
    'optimism': {
        'etherscan': f'https://api-optimistic.etherscan.io/api',
        'alchemy': f'https://opt-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}'
    },
    'mainnet': {
        'etherscan': 'https://api.etherscan.io/api',
        'alchemy': f'https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}'
    }
}

def is_eoa(chain, address):
    
    url = APIS[chain]['alchemy']
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "params": [address, "latest"],
        "method": "eth_getCode"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Error looking up address {address}")
        return None
    result = response.json()['result']
    return result == '0x'


def fetch_contract_name(chain, address):    
    
    try:
        url = APIS[chain]['etherscan']
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
            'apikey': ETHERSCAN_API_KEY
        }
        response = requests.get(url, params=params)
        if response.json()['status'] != '1':
            print(f"Error looking up a contract at address {address}")
            return None

        contract_name = response.json()['result'][0]['ContractName']
        if not contract_name:
            print(f"No contract/name associated with address {address}")
            return None
        
        print(f"{chain}: {address} -> {contract_name}")
        return contract_name    
    except:
        print(f"\n\n** Fatal error looking up a contract at address {address}\n\n")
        return None
