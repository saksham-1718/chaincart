import os
from cryptography.fernet import Fernet
from eth_account import Account
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

WALLET_ENCRYPTION_KEY = os.getenv("WALLET_ENCRYPTION_KEY")
GANACHE_URL = os.getenv("WEB3_RPC_URL", "http://127.0.0.1:7545")
DEPLOYER_PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # your existing backend/deployer key

if not WALLET_ENCRYPTION_KEY:
    raise RuntimeError("WALLET_ENCRYPTION_KEY is not set in .env")

fernet = Fernet(WALLET_ENCRYPTION_KEY.encode())
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))


def create_wallet():
    """Generate a brand new Ethereum keypair. Returns (address, encrypted_private_key_str)."""
    acct = Account.create()
    encrypted_key = fernet.encrypt(acct.key.hex().encode()).decode()
    return acct.address, encrypted_key


def decrypt_private_key(encrypted_key_str):
    """Decrypt a stored private key back to raw hex for signing a transaction."""
    return fernet.decrypt(encrypted_key_str.encode()).decode()


def fund_wallet(address, amount_eth=0.001):
    """Send fake ETH from the deployer/backend account to a new user's wallet, so they can pay gas."""
    if not w3.is_connected():
        print("⚠️ Cannot fund wallet — Ganache not reachable")
        return None

    deployer_account = w3.eth.account.from_key(DEPLOYER_PRIVATE_KEY)

    tx = {
        "from": deployer_account.address,
        "to": address,
        "value": w3.to_wei(amount_eth, "ether"),
        "nonce": w3.eth.get_transaction_count(deployer_account.address),
        "gas": 21000,
        "gasPrice": w3.eth.gas_price,    
        }
    signed_tx = w3.eth.account.sign_transaction(tx, DEPLOYER_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ Funded {address} with {amount_eth} ETH (test). Tx: {tx_hash.hex()}")
    return receipt