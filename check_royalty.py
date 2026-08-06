from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_RPC_URL')))
from contracts.interact_contract import contract

TX_HASH = '0xbcf3c125d70e4bb94a4cced994dcb53a3c76233184dadd508a4103d5502afe3f'

receipt = w3.eth.get_transaction_receipt(TX_HASH)
logs = contract.events.ArtworkPurchased().process_receipt(receipt)

if not logs:
    print("No ArtworkPurchased event found in this transaction.")
else:
    for log in logs:
        print(dict(log['args']))