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
    return list(collection.find({}, {"username": 1, "email": 1, "_id": 1, "trade_summary": 1, "broker_list": 1}))

st.title("Admin Panel")

# Fetch all admins
admins = fetch_admins()
if admins:
    st.subheader("Existing Admins")
    for admin in admins:
        col1, col2, col3 = st.columns([3, 1, 1])  # Create two columns: one for details, one for button

        with col1:
            st.write(f"**Username:** {admin['username']} | **Email:** {admin['email']}")

        with col2:
            if st.button(f"Show PnL", key=f"pnl_{admin['_id']}"):
                st.session_state[f"show_pnl_{admin['_id']}"] = not st.session_state.get(f"show_pnl_{admin['_id']}", False)

        with col3:
            if st.button(f"Show Broker", key=f"broker_{admin['_id']}"):
                st.session_state[f"show_broker_{admin['_id']}"] = not st.session_state.get(f"show_broker_{admin['_id']}", False)

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

        
        if st.session_state.get(f"show_broker_{admin['_id']}", False):
            with st.expander(f"Broker Info for {admin['username']}"):
                broker_list = admin.get("broker_list", ["Upstox", "Angel One"])  # Default brokers if none exist
        
                for broker in broker_list:
                    col_b1, col_b2 = st.columns([3, 1])  # Two columns: Broker Name | Add Broker Button
                    with col_b1:
                        st.write(f"🏦 **{broker}**")  # Broker name on the left
                    with col_b2:
                        if st.button("Add Broker", key=f"add_broker_{admin['_id']}_{broker}"):
                            st.session_state[f"add_broker_form_{admin['_id']}_{broker}"] = True
        
                # If any "Add Broker" button is clicked, show the form for that broker
                for broker in broker_list:
                    if st.session_state.get(f"add_broker_form_{admin['_id']}_{broker}", False):
                        with st.expander(f"Add Broker for {admin['username']}"):
                            new_broker = st.text_input("Enter Broker Name", key=f"broker_input_{admin['_id']}_{broker}")
                            if st.button("Submit Broker", key=f"submit_broker_{admin['_id']}_{broker}"):
                                # Here you would update the database with the new broker
                                st.success(f"Broker '{new_broker}' added successfully!")
                                st.session_state[f"add_broker_form_{admin['_id']}_{broker}"] = False  # Hide form after submission

        if st.session_state.get(f"add_broker_form_{admin['_id']}", False):
            with st.expander(f"Add Broker for {admin['username']}"):
                new_broker = st.text_input("Enter Broker Name", key=f"broker_input_{admin['_id']}")
                if st.button("Submit Broker", key=f"submit_broker_{admin['_id']}"):
                    # Here you would update the database with the new broker
                    st.success(f"Broker '{new_broker}' added successfully!")
                    st.session_state[f"add_broker_form_{admin['_id']}"] = False 

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
            "gmail_app_password": ""
        }

    with st.form("user_form"):
        username = st.text_input("Username", st.session_state.form_data["username"])
        password = st.text_input("Password", st.session_state.form_data["password"], type="password")
        email = st.text_input("Email", st.session_state.form_data["email"])
        phone = st.text_input("Phone", st.session_state.form_data["phone"])
        gmail_app_password = st.text_input("Gmail App Password", st.session_state.form_data["gmail_app_password"])
       
        submit = st.form_submit_button("Submit")

        if submit:
            hashed_password = hash_password(password)  # Hash the password before storing

            user_data = {
                "username": username,
                "password": hashed_password,  # Store hashed password
                "email": email,
                "phone": phone,
                "gmail_app_password": gmail_app_password,
                "imap_server": "imap.gmail.com"
            }
          #  store_to_mongo(user_data)
            st.success("Data stored successfully!")

            # Clear session state
            for key in st.session_state.form_data:
                st.session_state.form_data[key] = ""

            # Hide form after submission
            st.session_state.show_form = False
            st.rerun()