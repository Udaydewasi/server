from flask_cors import CORS
from flask import Flask, request, jsonify
import requests
from pymongo import MongoClient
import copy
from bson.objectid import ObjectId
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

client = MongoClient("mongodb+srv://test-yt:DYYAQ8YZ2d1XrdTb@test.ced18.mongodb.net/")
db = client["user_database"]
user_collection = db["users"]
broker_form_collection = db['broker form']
    
def stored_user_info(data) :

    if isinstance(data, dict): 
        user_collection.insert_one(data)
        print("Data inserted successfully")
    else:
        print("Error: Data must be a dictionary")

    return None
    
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

# def send_trade_history():

    
# admin form receiver
@app.route('/createUserForm', methods=['POST'])
def handle_admin_form():
    
    received_data = request.get_json()
    print(received_data)
    datas = copy.deepcopy(received_data) 
    stored_user_info(received_data)
    print("datas",datas)
    return jsonify(datas)

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
# @app.route('/get_trade_history', methods=['GET'])
# def get_user_detail():
#   #  user_detail = send_trade_history()
#  #   print(user_detail)
#  #   return jsonify(user_detail)
 
if __name__ == "__main__":  
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 6000)), debug=True)
