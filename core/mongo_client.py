from pymongo import MongoClient
import certifi

MONGO_URI = "mongodb+srv://sakshamsingh171845_db_user:Saksham1718@cluster0.6vepxmg.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["chaincart"]
