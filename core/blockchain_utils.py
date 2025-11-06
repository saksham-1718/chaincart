from contracts.interact_contract import list_artwork, get_artwork

def sync_artwork_to_blockchain(title, artist, price):
    try:
        tx_receipt = list_artwork(title, artist, int(price))
        print(f"✅ Artwork synced to blockchain. Tx Hash: {tx_receipt.transactionHash.hex()}")
        return tx_receipt
    except Exception as e:
        print("⚠️ Blockchain sync failed:", e)
        return None
