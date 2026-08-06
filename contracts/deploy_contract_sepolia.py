from web3 import Web3
import json, os
from dotenv import load_dotenv

load_dotenv()

SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL")
SEPOLIA_PRIVATE_KEY = os.getenv("SEPOLIA_PRIVATE_KEY")

if not SEPOLIA_RPC_URL:
    raise RuntimeError("SEPOLIA_RPC_URL is not set in .env")
if not SEPOLIA_PRIVATE_KEY:
    raise RuntimeError("SEPOLIA_PRIVATE_KEY is not set in .env")

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))

if not w3.is_connected():
    raise RuntimeError("Cannot connect to Sepolia. Check your SEPOLIA_RPC_URL.")

with open("contracts/build/ArtMarketplace.json") as f:
    compiled = json.load(f)

contract_data = compiled["contracts"]["ArtMarketplace.sol"]["ArtMarketplace"]
abi = contract_data["abi"]
bytecode = contract_data["evm"]["bytecode"]["object"]

deployer_account = w3.eth.account.from_key(SEPOLIA_PRIVATE_KEY)
deployer_address = deployer_account.address

balance = w3.eth.get_balance(deployer_address)
print(f"Deployer address: {deployer_address}")
print(f"Balance: {w3.from_wei(balance, 'ether')} SepoliaETH")

if balance == 0:
    raise RuntimeError("Deployer wallet has 0 Sepolia ETH — get funds from a faucet first.")

Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

tx = Contract.constructor().build_transaction({
    "from": deployer_address,
    "nonce": w3.eth.get_transaction_count(deployer_address),
    "gas": 3000000,
    "gasPrice": w3.eth.gas_price,
})

signed_tx = w3.eth.account.sign_transaction(tx, SEPOLIA_PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

print(f"Deployment transaction sent: {tx_hash.hex()}")
print("Waiting for confirmation (this can take 15-60 seconds on Sepolia)...")

tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"\n✅ Contract deployed to Sepolia at: {tx_receipt.contractAddress}")
print(f"   View on Etherscan: https://sepolia.etherscan.io/address/{tx_receipt.contractAddress}")
print(f"   Deployed from account: {deployer_address}")
print("\nAdd this to your .env as SEPOLIA_CONTRACT_ADDRESS")
