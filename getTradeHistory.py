from pymongo import MongoClient
from bson.objectid import ObjectId
import requests
from getAccessToken import get_access_token
from database import stored_datas
from datetime import datetime

def get_live_data(user_id, broker_name, count):
    
    client = MongoClient("mongodb+srv://test-yt:DYYAQ8YZ2d1XrdTb@test.ced18.mongodb.net/")
    db = client["user_database"]
    collection = db["users"]
    processDB = db["processCount"]
    today_date = datetime.today().strftime('%d-%m-%Y')
    
    document_id = ObjectId(user_id)
    
    user_doc = collection.find_one(
        {'_id': document_id},
        {f'{broker_name}': 1, '_id': 0}
    )
    
    if user_doc and broker_name in user_doc and user_doc[broker_name]:
        broker_data = user_doc[broker_name][0]
        access_token = broker_data.get('access_token')
        
        if access_token and is_token_active(access_token):
            trade_history = stored_datas(user_id, access_token)

    try:
        broker_data = user_doc[broker_name][0]
        doc = collection.find_one({'_id': document_id}, {'gmail': 1, '_id': 0})

        api_key = broker_data.get('api_key')
        secret_key = broker_data.get('secret_key')
        redirect_uri = broker_data.get('redirect_uri')
        phone_no = broker_data.get('phone')
        password = broker_data.get('pin')
        gmail_username = doc.get('gmail')
        gmail_app_password = broker_data.get('gmail_apppassword')
        imap_server = broker_data.get('imap_server')
        
        new_access_token = get_access_token(api_key, secret_key, redirect_uri, phone_no, password, gmail_username, gmail_app_password, imap_server)["code"]
        
        if new_access_token:
            collection.update_one(
                {
                    "_id": document_id,
                    f"{broker_name}": {"$exists": True}
                },
                {
                    "$set": {f"{broker_name}.0.access_token": new_access_token}
                }
            )

        trade_history = stored_datas(user_id, new_access_token)

        #insert into database with user_id, date, count
        processDB.update_one(
            {"user_id": user_id},
            {"$set": {f"{today_date}.count": count + 1, f"{today_date}.success": "true"}},
            upsert=True
        )

    except Exception as e:
        print(f"Error generating new access token: {str(e)}")
        # if count > 3 then don't push
            #push inside the database with user_id, date, count
        #insert into .txt file with count+1
        if count + 1 >= 3:
            processDB.update_one(
                {"user_id": user_id},
                {"$set": {f"{today_date}.count": count + 1, f"{today_date}.success": "false"}},
                upsert=True
            )
        else:
            with open("pending.txt", "a") as file:
                file.write(f"{user_id},{broker_name},{count + 1}\n")
        return None	
	
def is_token_active(access_token):
   
    url = "https://api.upstox.com/v2/user/profile"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    return response.status_code == 200 and "data" in response.json()


# get_live_data("67ac64ba8bc3b42e6c7f5ef7", "upstox")
print("function terminated")