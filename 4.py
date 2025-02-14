from pymongo import MongoClient
from bson.objectid import ObjectId
import json

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["user_database"]
collection = db["users"]

# Trade Data
trade_data = {
    "19-12-2024": {
        "total_buy_amount": 62240.0,
        "total_sell_amount": 62790.0,
        "total_pl": 550.0,
        "total_quantity": 1875.0
    },
    "08-01-2025": {
        "total_buy_amount": 8325.0,
        "total_sell_amount": 7477.5,
        "total_pl": -847.5,
        "total_quantity": 15000.0
    },
    "09-01-2025": {
        "total_buy_amount": 937.5,
        "total_sell_amount": 675.0,
        "total_pl": -262.5,
        "total_quantity": 3750.0
    },
    "10-01-2025": {
        "total_buy_amount": 937.5,
        "total_sell_amount": 675.0,
        "total_pl": -262.5,
        "total_quantity": 3750.0
    },
    "11-01-2025": {
        "total_buy_amount": 937.5,
        "total_sell_amount": 675.0,
        "total_pl": -262.5,
        "total_quantity": 3750.0
    },
    "12-01-2025": {
        "total_buy_amount": 937.5,
        "total_sell_amount": 675.0,
        "total_pl": -262.5,
        "total_quantity": 3750.0
    }
}
data = {
    "10-01-2025": {
        "total_buy_amount": 62240.0,
        "total_sell_amount": 62790.0,
        "total_pl": 550.0,
        "total_quantity": 1875.0
    },
}

# Convert trade data to list format for storage in an array
trade_summary_list = [{"date": date, **details} for date, details in trade_data.items()]

# Document ID
doc_id = "67a9dbcc6e3177edb06724bb"
document_id = ObjectId(doc_id)

# Update MongoDB document by appending trade summaries into an array
collection.update_one(
    {"_id": document_id},
    {"$push": {"trade_summary": {"$each": trade_summary_list}}}  # Append array to `trade_summary`
)

print("Trade data added successfully!")
