from contracts.interact_contract import list_artwork, get_artwork, get_id_from_receipt

def sync_artwork_to_blockchain(title, artist, price, artist_address, artist_private_key):
    """
    Lists an artwork on-chain, signed by the artist's own wallet.
    Returns (tx_receipt, chain_id) — chain_id is None if the sync failed.
    """
    try:
        tx_receipt = list_artwork(title, artist, int(price), artist_address, artist_private_key)
        if tx_receipt is None:
            return None, None

        chain_id = get_id_from_receipt(tx_receipt)
        print(f"✅ Artwork synced to blockchain. Tx Hash: {tx_receipt.transactionHash.hex()}, Chain ID: {chain_id}")
        return tx_receipt, chain_id
    except Exception as e:
        print("⚠️ Blockchain sync failed:", e)
        return None, None