import os
from dotenv import load_dotenv

load_dotenv()

def preview(name, full=False, tail=6):
    val = os.getenv(name)
    if val is None:
        return f"{name}: NOT SET"
    if full:
        return f"{name}: {val}"
    if len(val) <= tail:
        return f"{name}: (too short to preview safely, len={len(val)})"
    return f"{name}: ...{val[-tail:]}  (length={len(val)})"

print("=== Values Render's environment variables should match ===\n")

print(preview("SECRET_KEY"))
print(preview("DEBUG", full=True))
print(preview("DATABASE_URL"))
print(preview("MONGO_URI"))
print(preview("MONGO_DB_NAME", full=True))
print(preview("RAZORPAY_KEY_ID", full=True))
print(preview("RAZORPAY_KEY_SECRET"))

print("\n--- Blockchain: use SEPOLIA_* values below for Render's WEB3_RPC_URL / PRIVATE_KEY / CONTRACT_ADDRESS ---")
print(preview("SEPOLIA_CONTRACT_ADDRESS", full=True))
print(preview("SEPOLIA_RPC_URL"))
print(preview("SEPOLIA_PRIVATE_KEY"))

print("\n--- Local-only Ganache values (do NOT use these on Render) ---")
print(preview("WEB3_RPC_URL", full=True))
print(preview("CONTRACT_ADDRESS", full=True))
print(preview("PRIVATE_KEY"))

print("\n--- Wallets & Email ---")
print(preview("WALLET_ENCRYPTION_KEY"))
print(preview("EMAIL_HOST_USER", full=True))
print(preview("EMAIL_HOST_PASSWORD"))