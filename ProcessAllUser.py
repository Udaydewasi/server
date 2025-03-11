from pymongo import MongoClient
from getTradeHistory import get_live_data
import os
from datetime import datetime
import time

def processAllUser():

    client = MongoClient("mongodb+srv://test-yt:DYYAQ8YZ2d1XrdTb@test.ced18.mongodb.net/")
    db = client["user_database"]
    collection = db["users"]
    users = collection.find({"role": "user"})

    for user in users:
        user_id = str(user["_id"])
        
        if "broker_list" in user:
            for broker in user["broker_list"]:
                get_live_data(user_id, broker, 0)
                formatted_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                print("---------------------------------------------------------------------------",formatted_datetime)
                # time.sleep(60)

# Call the function to process all users
processAllUser()

def processPendingUsers():
    pending_file = "pending.txt"
    while os.path.exists(pending_file):
        with open(pending_file, "r") as file:
            lines = file.readlines()
        
        if not lines:
            os.remove(pending_file)  # Remove empty file
            return
        
        first_entry = lines[0].strip()
        remaining_entries = lines[1:]

        with open(pending_file, "w") as file:
            file.writelines(remaining_entries)
        
        if not remaining_entries:
            os.remove(pending_file)
        
        user_id, broker_name, count = first_entry.split(",")
        get_live_data(user_id, broker_name, int(count))

        formatted_datetime = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        print("---------------------------------------------------------------------------",formatted_datetime)
        # time.sleep(60)

processPendingUsers()