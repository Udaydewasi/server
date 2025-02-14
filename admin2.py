import hashlib
import streamlit as st
import sqlite3
from pymongo import MongoClient
from automate2 import get_access_token
from database import stored_datas
from bson import ObjectId

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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

def store_to_mongo(data):
    client = MongoClient("mongodb://localhost:27017/")
    db = client["user_database"]
    collection = db["users"]
    insert_result = collection.insert_one(data)
    user_id = insert_result.inserted_id
    
    acc_token = get_request(user_id)
    print(acc_token)
    stored_datas(user_id, acc_token)

import streamlit as st
from pymongo import MongoClient

def fetch_admins():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["user_database"]
    collection = db["users"]
    return list(collection.find({}, {"username": 1, "email": 1, "_id": 1, "trade_summary": 1}))

st.title("Admin Panel")

# Fetch all admins
admins = fetch_admins()
if admins:
    st.subheader("Existing Admins")
    for admin in admins:
        col1, col2 = st.columns([3, 1])  # Create two columns: one for details, one for button

        with col1:
            st.write(f"**Username:** {admin['username']} | **Email:** {admin['email']}")

        with col2:
            if st.button(f"Show PnL", key=str(admin['_id'])):
                st.session_state[f"show_pnl_{admin['_id']}"] = not st.session_state.get(f"show_pnl_{admin['_id']}", False)

        # Check if PnL should be displayed
        if st.session_state.get(f"show_pnl_{admin['_id']}", False):
            with st.expander(f"PnL for {admin['username']}"):
                for trade in admin["trade_summary"]:
                    st.write(f"📅 **Date:** {trade['date']}")
                    st.write(f"🔹 **Total Buy Amount:** {trade['total_buy_amount']}")
                    st.write(f"🔹 **Total Sell Amount:** {trade['total_sell_amount']}")
                    st.write(f"🔹 **Total P&L:** {trade['total_pl']}")
                    st.write(f"🔹 **Total Quantity:** {trade['total_quantity']}")
                    st.markdown("---")  # Separator

# "New Admin" Button
if "show_form" not in st.session_state:
    st.session_state.show_form = False

if st.button("New Admin"):
    st.session_state.show_form = True

# Show the form if the button is clicked
if st.session_state.show_form:
    st.title("User Information Form")

    # Initialize session state for form fields
    if "form_data" not in st.session_state:
        st.session_state.form_data = {
            "username": "",
            "password": "",
            "email": "",
            "phone": "",
            "pin": "",
            "broker": "Upstox",
            "apikey": "",
            "redirect_uri": "",
            "secretkey": "",
            "gmail_username": "",
            "gmail_app_password": ""
        }

    with st.form("user_form"):
        username = st.text_input("Username", st.session_state.form_data["username"])
        password = st.text_input("Password", st.session_state.form_data["password"], type="password")
        email = st.text_input("Email", st.session_state.form_data["email"])
        phone = st.text_input("Phone", st.session_state.form_data["phone"])
        pin = st.text_input("Pin", st.session_state.form_data["pin"])
        broker = st.selectbox("Select Broker", ["Upstox", "Angel One"], index=0)
        apikey = st.text_input("API Key", st.session_state.form_data["apikey"])
        secretkey = st.text_input("Secret Key", st.session_state.form_data["secretkey"])
        redirect_uri = st.text_input("Redirect URI", st.session_state.form_data["redirect_uri"])
        gmail_username = st.text_input("Gmail Username", st.session_state.form_data["gmail_username"])
        gmail_app_password = st.text_input("Gmail App Password", st.session_state.form_data["gmail_app_password"])
       
        submit = st.form_submit_button("Submit")

        if submit:
            hashed_password = hash_password(password)  # Hash the password before storing

            user_data = {
                "username": username,
                "password": hashed_password,  # Store hashed password
                "email": email,
                "phone": phone,
                "pin": pin,
                "broker":broker,
                "apikey": apikey,
                "redirect_uri": redirect_uri,
                "secretkey": secretkey,
                "access_token": "",
                "trade_summary": [],
                "gmail_username": gmail_username,
                "gmail_app_password": gmail_app_password,
                "imap_server": "imap.gmail.com"
            }
            store_to_mongo(user_data)
            st.success("Data stored successfully!")

            # Clear session state
            for key in st.session_state.form_data:
                st.session_state.form_data[key] = ""

            # Hide form after submission
            st.session_state.show_form = False
            st.rerun()