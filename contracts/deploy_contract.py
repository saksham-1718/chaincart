from web3 import Web3
import json, os
from dotenv import load_dotenv

load_dotenv()

GANACHE_URL = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if not w3.is_connected():
    raise RuntimeError("Cannot connect to Ganache. Is the Ganache app running?")

with open("contracts/build/ArtMarketplace.json") as f:
    compiled = json.load(f)

contract_data = compiled["contracts"]["ArtMarketplace.sol"]["ArtMarketplace"]
abi = contract_data["abi"]
bytecode = contract_data["evm"]["bytecode"]["object"]

# Use Ganache's first pre-funded test account to deploy
deployer = w3.eth.accounts[0]

Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = Contract.constructor().transact({"from": deployer, "gas": 3000000})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"✅ Contract deployed at: {tx_receipt.contractAddress}")
print(f"   Deployed from account: {deployer}")