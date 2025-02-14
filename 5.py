from pymongo import MongoClient
from bson.objectid import ObjectId
# Connect to MongoDB
client = MongoClient("mongodb+srv://test-yt:DYYAQ8YZ2d1XrdTb@test.ced18.mongodb.net/")
db = client["user_database"]
collection = db["users"]

# Upstox data with trade_summary inside
upstox_data = {
    "pin": 105561,
    "api_key": "dsjnkkkjkkkkkkkkkkkjf",
    "secret_key": "dsjfjkhbhkbhb",
    "redirect_uri": "http://localhost",
    "gmail_apppassword": "welqewjiklewjiljqq",
    "trade_summary": {
        "19-01-2024": {
            "total_buy_amount": 62240.0,
            "total_sell_amount": 62790.0,
            "total_pl": 550.0,
            "total_quantity": 1875.0
        },
         "25-01-2024": {
            "total_buy_amount": 62240.0,
            "total_sell_amount": 62790.0,
            "total_pl": 5500.0,
            "total_quantity": 1875.0
        },
         "26-02-2024": {
            "total_buy_amount": 62240.0,
            "total_sell_amount": 62790.0,
            "total_pl": -5050.0,
            "total_quantity": 1875.0
        },
         "22-03-2024": {
            "total_buy_amount": 62240.0,
            "total_sell_amount": 62790.0,
            "total_pl": -150.0,
            "total_quantity": 1875.0
        },
        "12-02-2025": {
            "total_buy_amount": 8325.0,
            "total_sell_amount": 7477.5,
            "total_pl": 847.5,
            "total_quantity": 15000.0
        },
        "13-02-2025": {
            "total_buy_amount": 937.5,
            "total_sell_amount": 675.0,
            "total_pl": 262.5,
            "total_quantity": 370.0
        }
    }
}

doc_id = "67a9dbcc6e3177edb06724bb"
document_id = ObjectId(doc_id)
# Update MongoDB document by appending to `upstox` array
collection.update_one(
    {"_id": document_id},  # Match document by `_id`
    {"$push": {"zerodha": upstox_data}}  # Append new entry into `upstox` array
)

print("Document updated successfully!")

