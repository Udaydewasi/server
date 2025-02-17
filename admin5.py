from flask_cors import CORS
from flask import Flask, request, jsonify
import requests
from pymongo import MongoClient
import copy
from bson.objectid import ObjectId
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://p-l-page.vercel.app", "http://localhost:3000"]}}, supports_credentials=True)

client = MongoClient("mongodb+srv://test-yt:DYYAQ8YZ2d1XrdTb@test.ced18.mongodb.net/")
db = client["user_database"]
user_collection = db["users"]
broker_form_collection = db['broker form']
    
def stored_user_info(data):
    print(data)

    if not isinstance(data, dict): 
        print("Error: Data must be a dictionary")
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

    # If no duplicates, insert new user
    user_collection.insert_one(data)
    print("Data inserted successfully")
    return {"message": "User registered successfully"}
    
def stored_broker_info(data):
    broker_name = data.get('broker')
    info = {
        "phone":data.get("phone"),
        "pin":data.get('pin'),
        "api_key": data.get('api_key'),
        "secret_key": data.get('secret_key'),
        "redirect_uri": data.get('redirect_uri'),
        "gmail_apppassword": data.get('gmail_apppassword'),
    }

    user_collection.update_one(
        {"gmail": data.get('gmail')},  # Match by email
        {
            "$push": {broker_name: info},  # Store broker info
            "$addToSet": {"broker_list": broker_name}  # Store broker name in a list (avoid duplicates)
        }
    )
    return None

def send_user_detail():
    return list(user_collection.find({}, {"username": 1, "gmail": 1 , "_id" : 0}))

def send_broker_form():
    document = broker_form_collection.find_one({}, {"_id": 0}) 
    return document

def send_trade_history(user_email):
    
    user_data = user_collection.find_one({"gmail": user_email}, {"broker_list": 1, "_id": 0})  
    if not user_data or "broker_list" not in user_data:
        return {"message": "No brokers found for this user."}
    
    broker_list = user_data["broker_list"]  # Extract broker names
    projection = {f"{broker}.trade_summary": 1 for broker in broker_list}  
    projection["_id"] = 0  # Exclude `_id`
    broker_details = user_collection.find_one({"gmail": user_email}, projection)    

    return broker_details

def send_all_trade_history(user_email):
    return list(user_collection.find({"gmail": user_email}, {"all_trade_history": 1, "_id" : 0}))

def check_user(data):
    
    user = user_collection.find_one({"$or": [{"username": data['username']}, {"gmail": data['username']}]})
    print(user)
    if not user:
        return " Gmail is incorrect"
    
    # Check password
    if user["password"] != data['password']:
        return "Password is incorrect."

    return "User logged in successfully."

# admin form receiver
@app.route('/createUserForm', methods=['POST'])
def handle_admin_form():
    
    received_data = request.get_json()
    print(received_data)
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
    print(user_detail)
    return jsonify(user_detail)

@app.route('/get_broker_form', methods=['GET'])
def get_broker_form():
    broker_form = send_broker_form()
    print(broker_form)
    return broker_form

# user detail receiver for home page
@app.route('/get_trade_history', methods=['GET'])
def get_trade_history():
   gmail = request.args.get('gmail')
   print(gmail)
   user_detail = send_trade_history(gmail)
   print(user_detail)
   return jsonify(user_detail)

@app.route('/get_all_trade_history', methods=['GET'])
def get_all_trade_history():
   gmail = request.args.get('gmail')
   print(gmail)
   user_detail = send_all_trade_history(gmail)
   print(user_detail)
   return jsonify(user_detail)

@app.route('/checkUserCredential', methods=['POST'])
def check_user_credential():
    
    received_data = request.get_json()
    response = check_user(received_data)
    return jsonify(response)
 
if __name__ == "__main__":  
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 6000)), debug=True)
