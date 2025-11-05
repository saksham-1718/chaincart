from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://sakshamsingh171845_db_user:Saksham1718@cluster0.6vepxmg.mongodb.net/?appName=Cluster0")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "chaincart")

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Collections
users_col = db["users"]
products_col = db["products"]
transactions_col = db["transactions"]
royalties_col = db["royalties"]

# -----------------------------
# Example helper functions
# -----------------------------

def add_user(user_data: dict):
    """Insert a new user (artist or buyer)."""
    user_data["created_at"] = datetime.utcnow()
    return users_col.insert_one(user_data)

def add_product(product_data: dict):
    """Insert a new product (artwork)."""
    product_data["created_at"] = datetime.utcnow()
    product_data.setdefault("royalty_percent", 10)
    return products_col.insert_one(product_data)

def record_transaction(tx_data: dict):
    """Insert a blockchain transaction record."""
    tx_data["timestamp"] = datetime.utcnow()
    return transactions_col.insert_one(tx_data)

def record_royalty(royalty_data: dict):
    """Log royalty payment."""
    royalty_data["timestamp"] = datetime.utcnow()
    return royalties_col.insert_one(royalty_data)

def get_user_by_email(email: str):
    return users_col.find_one({"email": email})

def get_product_by_id(pid):
    return products_col.find_one({"_id": pid})
