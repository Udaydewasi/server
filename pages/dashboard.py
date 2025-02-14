import streamlit as st
import requests
from datetime import datetime
from automate2 import get_access_token
from pymongo import MongoClient
from bson.objectid import ObjectId

# Define access token

def is_token_active(access_token):
   
    url = "https://api.upstox.com/v2/user/profile"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    return response.status_code == 200 and "data" in response.json()

def get_current_pnl(access_token):
    
    url = 'https://api.upstox.com/v2/portfolio/short-term-positions'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    return response.json()

def get_only_pnl(data):
 
    if not isinstance(data, dict) or 'data' not in data:
        return 0

    return sum(trade.get('pnl', 0) for trade in data['data'] if trade.get('quantity', 0) != 0)

def find_data(doc_id) :

    client = MongoClient("mongodb://localhost:27017/")
    db = client["user_database"]
    collection = db["users"]
    one = collection.find_one({'_id': ObjectId(doc_id)}, {'trade_summary': 1, '_id': 0})
    return one['trade_summary']

def filter_data_between_dates(data, start_date, end_date):

    start_date = str(start_date)
    end_date  =  str(end_date)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # Filter list based on date range
    filtered_data = [
        entry for entry in data
        if start <= datetime.strptime(entry["date"], "%d-%m-%Y") <= end
    ]
    
    return filtered_data

def get_request(user_id) :

    client = MongoClient("mongodb://localhost:27017/")
    db = client['user_database']
    collection = db['users'] 

    # Fetch user document
    user_data = collection.find_one({"_id": ObjectId(user_id)})

    if not user_data:
        print("User not found!")
        return None

    # Extract required fields
    api_key = user_data.get("apikey")
    secret_key = user_data.get("secretkey")
    redirect_uri = user_data.get("redirect_uri")
    phone_no = user_data.get("phone")
    password = user_data.get("pin")
    gmail_username = user_data.get("gmail_username")
    gmail_app_password = user_data.get("gmail_app_password")
    imap_server = user_data.get("imap_server")

    # Call function with extracted values
    acc_token = get_access_token(api_key, secret_key, redirect_uri, phone_no, password, gmail_username, gmail_app_password, imap_server)
    return acc_token

def get_live_data(user_id):

    client = MongoClient("mongodb://localhost:27017/")
    db = client['user_database']
    collection = db['users']
    
    document_id = ObjectId(user_id)
    doc = collection.find_one({'_id': document_id}, {'access_token': 1, '_id': 0})
    access_token = doc.get('access_token')
    
    if not is_token_active(access_token) or access_token == "None" :
        access_token = get_request(user_id)
        #access_token = get_access_token()

        collection.update_one(
            {"_id":  ObjectId(document_id)},  # Filter condition
            {"$set": {"access_token": access_token}}  # Updating only 'access_token'
        )

    current_data = get_current_pnl(access_token) # extract current p&l
    current_pl = get_only_pnl(current_data) # extract only p&l
    return current_pl

# Mock function to simulate fetching P&L data from MongoDB
def get_trade_summary(user_id, start_date, end_date):

    client = MongoClient("mongodb://localhost:27017/")
    db = client['user_database']
    collection = db['users']

    document_id = ObjectId(user_id)
    doc = collection.find_one({'_id': document_id}, {'access_token': 1, '_id': 0})
    access_token = doc.get('access_token')

    if not is_token_active(access_token) or access_token == "None" :
        access_token = get_request(user_id)
       # access_token = get_access_token()

        collection.update_one(
            {"_id":  ObjectId(document_id)},  # Filter condition
            {"$set": {"access_token": access_token}}  # Updating only 'access_token'
        )

    data = find_data(user_id)
    result = filter_data_between_dates(data, start_date, end_date)
    return result

def dashboard():
    """Render the Dashboard UI."""
    # Check if user is authenticated
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        st.warning("⚠️ Please log in to view the dashboard.")
        return  # Stop execution if user is not authenticated

    st.title("Dashboard")
    st.success("✅ You are logged in!")

    # Initialize session state for live P&L value
    if "function_value" not in st.session_state:
        st.session_state["function_value"] = get_live_data(st.session_state['user_id'])

    # Display function value
    value_placeholder = st.empty()
    value_placeholder.write(f"Overall P&L : {st.session_state['function_value']}")

    # Refresh Button
    if st.button("Refresh"):
        st.session_state["function_value"] = get_live_data(st.session_state['user_id'])
        value_placeholder.write(f"Overall P&L : {st.session_state['function_value']}")

    st.subheader("📅 Select Date Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime(2024, 12, 19))
    with col2:
        end_date = st.date_input("End Date", datetime(2025, 1, 9))

    # OK Button to fetch data
    if st.button("OK"):
        result = get_trade_summary(st.session_state['user_id'], start_date, end_date)
      #  st.write(result)
        for entry in result:
             st.write(f"Date : {entry['date']} , Total P&L : {entry['total_pl']}")

if __name__ == "__main__":
    dashboard()
