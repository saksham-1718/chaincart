from web3 import Web3
import json, os
from dotenv import load_dotenv

# ================================================
# 🌍 Load environment variables
# ================================================
load_dotenv()

WEB3_RPC_URL = os.getenv("WEB3_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

# ================================================
# 🔗 Initialize Web3 (Safe Mode for Dev)
# ================================================
w3 = None
account = None
contract = None

if WEB3_RPC_URL:
    try:
        w3 = Web3(Web3.HTTPProvider(WEB3_RPC_URL))
        if w3.is_connected():
            print("✅ Web3 connected successfully")
        else:
            print("⚠️ Web3 provider not reachable")
    except Exception as e:
        print(f"⚠️ Web3 connection failed: {e}")
else:
    print("⚠️ WEB3_RPC_URL not set — Blockchain features disabled.")

# ================================================
# 🔐 Initialize Account (Safe)
# ================================================
if PRIVATE_KEY and len(PRIVATE_KEY) == 66 and PRIVATE_KEY.startswith("0x"):
    try:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        print(f"✅ Account loaded: {account.address}")
    except Exception as e:
        print(f"⚠️ Failed to load account: {e}")
else:
    print("⚠️ PRIVATE_KEY not set or invalid — Blockchain tx disabled.")

# ================================================
# 📄 Load Contract ABI & Connect
# ================================================
try:
    with open("contracts/build/ArtMarketplace.json") as f:
        compiled = json.load(f)

    abi = compiled["contracts"]["ArtMarketplace.sol"]["ArtMarketplace"]["abi"]

    if w3 and CONTRACT_ADDRESS:
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
        print("✅ Contract loaded successfully")
    else:
        print("⚠️ Contract not loaded (missing Web3 or CONTRACT_ADDRESS).")

except FileNotFoundError:
    print("⚠️ Contract ABI file not found — please compile your contract first.")
except Exception as e:
    print(f"⚠️ Error loading contract: {e}")

# ================================================
# 🎨 Blockchain Interaction Functions
# ================================================
def list_artwork(title, artist, price, artist_address, artist_private_key):
    """List a new artwork on the blockchain — signed by the ARTIST's own wallet."""
    if not (w3 and contract):
        print("⚠️ Blockchain not configured — skipping list_artwork()")
        return None

    try:
        tx = contract.functions.listArtwork(title, artist, price).build_transaction({
            "from": artist_address,
            "nonce": w3.eth.get_transaction_count(artist_address),
            "gas": 3000000,
            "gasPrice": w3.to_wei("2", "gwei"),
        })
        signed_tx = w3.eth.account.sign_transaction(tx, artist_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Artwork listed successfully! Tx Hash: {tx_hash.hex()}")
        return receipt
    except Exception as e:
        print(f"⚠️ Failed to list artwork: {e}")
        return None


def get_artwork(id):
    """Retrieve artwork details"""
    if not contract:
        print("⚠️ Contract not loaded — skipping get_artwork()")
        return None
    try:
        return contract.functions.getArtwork(id).call()
    except Exception as e:
        print(f"⚠️ Failed to fetch artwork: {e}")
        return None


def relist_artwork(id, new_price, owner_address, owner_private_key):
    """Relist an artwork — must be signed by the CURRENT OWNER's own wallet."""
    if not (w3 and contract):
        print("⚠️ Blockchain not configured — skipping relist_artwork()")
        return None

    try:
        tx = contract.functions.relistArtwork(id, new_price).build_transaction({
            'from': owner_address,
            'nonce': w3.eth.get_transaction_count(owner_address),
            'gas': 3000000,
            'gasPrice': w3.to_wei('2', 'gwei'),
        })
        signed_tx = w3.eth.account.sign_transaction(tx, owner_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Artwork relisted successfully! Tx Hash: {tx_hash.hex()}")
        return receipt
    except Exception as e:
        print(f"⚠️ Failed to relist artwork: {e}")
        return None


def get_id_from_receipt(receipt):
    """Extract the artwork ID emitted by the ArtworkListed event in a transaction receipt."""
    if not contract or not receipt:
        return None
    try:
        logs = contract.events.ArtworkListed().process_receipt(receipt)
        if logs:
            return logs[0]["args"]["id"]
    except Exception as e:
        print(f"⚠️ Failed to parse ArtworkListed event: {e}")
    return None


def buy_artwork(id, price, buyer_address, buyer_private_key):
    """Buy an artwork on-chain, signed by the BUYER's own wallet (not the backend's)."""
    if not (w3 and contract):
        print("⚠️ Blockchain not configured — skipping buy_artwork()")
        return None

    try:
        tx = contract.functions.buyArtwork(id).build_transaction({
            "from": buyer_address,
            "value": price,  # price is stored on-chain as a plain integer — see note below
            "nonce": w3.eth.get_transaction_count(buyer_address),
            "gas": 3000000,
            "gasPrice": w3.to_wei("2", "gwei"),
        })
        signed_tx = w3.eth.account.sign_transaction(tx, buyer_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Artwork purchased on-chain! Tx Hash: {tx_hash.hex()}")
        return receipt
    except Exception as e:
        print(f"⚠️ Failed to buy artwork: {e}")
        return None