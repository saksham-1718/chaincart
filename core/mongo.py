from pymongo import MongoClient
import certifi
import os
from dotenv import load_dotenv
from datetime import datetime
import gridfs


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "chaincart")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set in .env — check your environment configuration.")

# tlsCAFile=certifi.where() avoids SSL certificate errors on Windows when
# connecting to Atlas — Windows' default cert store often doesn't satisfy pymongo.
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client[MONGO_DB_NAME]

users_col = db["users"]
products_col = db["products"]
transactions_col = db["transactions"]
royalties_col = db["royalties"]


def add_user(user_data: dict):
    user_data["created_at"] = datetime.utcnow()
    return users_col.insert_one(user_data)

def add_product(product_data: dict):
    product_data["created_at"] = datetime.utcnow()
    product_data.setdefault("royalty_percent", 10)
    return products_col.insert_one(product_data)

def record_transaction(tx_data: dict):
    tx_data["timestamp"] = datetime.utcnow()
    return transactions_col.insert_one(tx_data)

def record_royalty(royalty_data: dict):
    royalty_data["timestamp"] = datetime.utcnow()
    return royalties_col.insert_one(royalty_data)

def get_user_by_email(email: str):
    return users_col.find_one({"email": email})

def get_product_by_id(pid):
    return products_col.find_one({"_id": pid})




def save_image_to_gridfs(file_obj):
    """Saves an uploaded file to GridFS and returns its string ID."""
    fs = gridfs.GridFS(db)
    image_id = fs.put(file_obj, filename=file_obj.name)
    return str(image_id)