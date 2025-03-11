from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import copy
from getAccessToken import get_access_token

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://p-l-page.vercel.app", "http://localhost:3000"]}}, supports_credentials=True)

client = MongoClient("mongodb+srv://test-yt:DYYAQ8YZ2d1XrdTb@test.ced18.mongodb.net/")
db = client["user_database"]
user_collection = db["users"]
broker_form_collection = db['broker form']
    
def stored_user_info(data):
    if not isinstance(data, dict): 
        return {"error": "Invalid data format"}

    # Check if username or gmail already exists
    existing_user = user_collection.find_one(
        {"$or": [{"username": data["username"]}, {"gmail": data["gmail"]}]}
    )

    if existing_user:
        if existing_user["username"] == data["username"]:
            return {"error": "Username already exists"}
        elif existing_user["gmail"] == data["gmail"]:
            return {"error": "Gmail already exists"}
            
    user_collection.insert_one(data)
    return {"message": "User registered successfully"}
    
def stored_broker_info(data):
    broker_name = data.get('broker')
    gmail = data.get('gmail')

    user_collection.update_one(
        {"gmail": gmail}, {"$unset": {broker_name: ""}}
    )

    info = {
        "phone":data.get("phone"),
        "pin":data.get('pin'),
        "api_key": data.get('api_key'),
        "secret_key": data.get('secret_key'),
        "redirect_uri": data.get('redirect_uri'),
        "gmail_apppassword": data.get('gmail_apppassword'),
        "imap_server": data.get('imap_server'),
        "visible": "true",
        "tested": "false",
        "trade_summary": {}
    }

    user_collection.update_one(
        {"gmail": gmail},
        {
            "$push": {broker_name: info},
            "$addToSet": {"broker_list": broker_name}
        }
    )

    return {"success": True, "message": f"{broker_name} info updated"}

def send_user_detail():
    return list(user_collection.find({"role": "user"}, {"username": 1, "gmail": 1 , "_id" : 0}))

def send_broker_form():
    document = broker_form_collection.find_one({}, {"_id": 0}) 
    return document

def getBrokerDetails(data):
    gmail = data.get('gmail')
    broker = data.get('broker')

    projection = {f"{broker}.trade_summary": 0, f"{broker}.visible": 0, f"{broker}.access_token": 0, "_id": 0}
    user_data = user_collection.find_one({"gmail": gmail}, projection)
    
    return user_data[broker]
    

def send_trade_history(user_email):
    user_data = user_collection.find_one({"gmail": user_email}, {"broker_list": 1, "_id": 0})
    broker_list = user_data["broker_list"]  # Extract broker names

    if not user_data or "broker_list" not in user_data:
        return {"message": "No user data found for this user."}

    if not broker_list:
        return {"message": "No brokers found for this user."}
    
    projection = {f"{broker}.trade_summary": 1 for broker in broker_list}  
    projection["_id"] = 0  # Exclude `_id`
    broker_details = user_collection.find_one({"gmail": user_email}, projection)  
    return broker_details

def send_all_trade_history(user_email):
    return list(user_collection.find({"gmail": user_email}, {"all_trade_history": 1, "_id" : 0}))

def check_user(data):
    
    user = user_collection.find_one({"$or": [{"username": data['username']}, {"gmail": data['username']}]})
    if not user:
        return " Gmail is incorrect"

    if user["password"] != data['password']:
        return "Password is incorrect."

    if user.get('role') != data['role']:
        return {"error": "Unauthorized for this role"}, 403
    
    user_data = {
        "message": "Login successful",
        "user": {
            "id": str(user['_id']),
            "username": user['username'],
            "gmail": user['gmail'],
            "role": user['role']
        }
    }
    return user_data, 200

# mark invisble broker and delete the entry from brokerlist
def mark_broker_false(data):
    gmail = data.get("gmail")
    broker_name = data.get("broker")

    if not gmail or not broker_name:
        return {"error": "Missing gmail or broker_name"}

    user = user_collection.find_one({"gmail": gmail})
    if not user:
        return {"error": "User not found"}

    # Remove broker from broker_list
    new_broker_list = [b for b in user["broker_list"] if b != broker_name]

    if broker_name in user:
        user_collection.update_one(
            {"gmail": gmail},
            {"$set": {f"{broker_name}.0.visible": "false"}}
        )

    user_collection.update_one(
        {"gmail": gmail},
        {"$set": {"broker_list": new_broker_list}}
    )

    return {"success": True, "message": f"{broker_name} removed from broker_list"}

# edit broker details fields
def update_broker(data):
    gmail = data.get("gmail")
    broker = data.get("broker")
    
    update_fields = {key: value for key, value in data.items() if key not in ["gmail", "broker", "visible"]}
    result = user_collection.update_one(
        {"gmail": gmail, f"{broker}.visible": "true"},
        {"$set": {f"{broker}.$.{key}": value for key, value in update_fields.items()}}
    )

    return "Broker Information Updated Successfully."
    
# test the broker details are working
def broker_testing(gmail, broker):
    user = user_collection.find_one({'gmail': gmail})
    broker_data = user[broker][0]
    
    api_key = broker_data.get('api_key')
    secret_key = broker_data.get('secret_key')
    redirect_uri = broker_data.get('redirect_uri')
    phone_no = broker_data.get('phone')
    password = broker_data.get('pin')
    gmail_username = gmail
    gmail_app_password = broker_data.get('gmail_apppassword')
    imap_server = broker_data.get('imap_server')

    response = get_access_token(api_key, secret_key, redirect_uri, phone_no, password, gmail_username, gmail_app_password, imap_server)

    if response["status"] == "success":
        user_collection.update_one({"gmail": gmail},
            {"$set": {f"{broker}.0.tested": "true"}}
        )

    return response


def status_test(gmail, broker):
    user = user_collection.find_one({"gmail": gmail},{f"{broker}.tested": 1, "_id": 0})
    
    if user and broker in user and len(user[broker]) > 0:
        return user[broker][0]["tested"]
    
    return None

# admin form receiver
@app.route('/createUserForm', methods=['POST'])
def handle_admin_form():
    
    received_data = request.get_json()
    response = stored_user_info(received_data)
    return jsonify(response)

# broker form receiver
@app.route('/addBrokerForm', methods=['POST'])
def handle_broker_form():
    
    received_data = request.get_json()
    datas = copy.deepcopy(received_data)
    stored_broker_info(received_data)
    return jsonify(datas)

# user detail receiver for home page
@app.route('/get_user_detail', methods=['GET'])
def get_user_detail():
    user_detail = send_user_detail()
    return jsonify(user_detail)

@app.route('/get_broker_form', methods=['GET'])
def get_broker_form():
    broker_form = send_broker_form()
    return broker_form

@app.route('/get_broker_details', methods=['GET'])
def BrokerDetails():
    gmail = request.args.get("gmail")
    broker = request.args.get("broker")
    received_data = {"gmail": gmail, "broker": broker}
    data = getBrokerDetails(received_data)
    return data

# user detail receiver for home page
@app.route('/get_trade_history', methods=['GET'])
def get_trade_history():
   gmail = request.args.get('gmail')
   user_detail = send_trade_history(gmail)
   return jsonify(user_detail)

@app.route('/get_all_trade_history', methods=['GET'])
def get_all_trade_history():
   gmail = request.args.get('gmail')
   user_detail = send_all_trade_history(gmail)
   return jsonify(user_detail)

@app.route('/checkUserCredential', methods=['POST'])
def check_user_credential():
    
    received_data = request.get_json()
    response = check_user(received_data)
    return jsonify(response)

@app.route('/deleteBroker', methods=['POST'])
def broker_delete():
    received_data = request.get_json()
    response = mark_broker_false(received_data)
    return jsonify(response)

@app.route('/editBroker', methods=['POST'])
def broker_edit():
    received_data = request.get_json()
    response = update_broker(received_data)
    return jsonify(response)

@app.route('/testbroker', methods=['GET'])
def broker_test():
    gmail = request.args.get('gmail')
    broker = request.args.get('broker')
    response = broker_testing(gmail, broker)
    return jsonify(response)
 

@app.route('/teststatus', methods=['GET'])
def test_status():
    gmail = request.args.get('gmail')
    broker = request.args.get('broker')
    response = status_test(gmail, broker)
    return jsonify(response)

if __name__ == "__main__":  
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
