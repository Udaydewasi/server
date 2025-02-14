from flask import Flask, request, jsonify
import requests
from pymongo import MongoClient
import copy
from bson.objectid import ObjectId


client = MongoClient("mongodb+srv://test-yt:DYYAQ8YZ2d1XrdTb@test.ced18.mongodb.net/")
db = client["user_database"]
collection = db["broker form"]

# create broker
def add_broker_form(broker_name, form_data):
    collection.update_one(
        {"_id": "brokers"},       
        {"$set": {broker_name: form_data}},
        upsert=True    
    )

    print(f"Broker '{broker_name}' data saved successfully!")

# delete broker 
def delete_broker(broker_name):
    collection.update_one(
        {"_id": "brokers"}, 
        {"$unset": {broker_name: ""}} 
    )

    print(f"Broker '{broker_name}' deleted successfully!")

form_data = ["pin", "api_key", "secret_key", "redirect_uri", "gmail_apppassword"]
add_broker_form("upstox", form_data)

# Example usage
delete_broker("upstox")