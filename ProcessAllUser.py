from pymongo import MongoClient
from getTradeHistory import get_live_data

def processAllUser():

    client = MongoClient("mongodb+srv://test-yt:DYYAQ8YZ2d1XrdTb@test.ced18.mongodb.net/")
    db = client["user_database"]
    collection = db["users"]
    users = collection.find({})

    for user in users:
        user_id = str(user["_id"])
        
        if "broker_list" in user:
            for broker in user["broker_list"]:
                # broker_name = broker.get("name", "Unknown Broker")
                print("broker name: ", broker)
                get_live_data(user_id, broker)


# Call the function to process all users
processAllUser()
