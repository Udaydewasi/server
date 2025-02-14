import streamlit as st
from pymongo import MongoClient
import hashlib

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")  # Change this to your MongoDB connection string
db = client["user_database"]  # Database Name
users_collection = db["users"]  # Collection Name

# Function to Hash Password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to Verify User Credentials
def check_credentials(username_or_email_or_phone, password):
    user = users_collection.find_one({
        "$or": [
            {"username": username_or_email_or_phone},
            {"email": username_or_email_or_phone},
            {"phone": username_or_email_or_phone}
        ]
    })
    
    if user and user["password"] == hash_password(password):
        return user["_id"]
    return None

# Streamlit UI
def main():
    st.title("User Access Check")
    st.subheader("Enter Your Username and Password to Verify Access")

    username = st.text_input("Phone number, username or email address")
    password = st.text_input("Password", type="password")

    if st.button("Check Access"):
        user_id = check_credentials(username, password)
        if user_id:
            st.success(f"✅ Access Granted! Welcome, {username}.")
            st.session_state['authenticated'] = True  # Store login state
            st.session_state['user'] = username  # Store username
            st.session_state['user_id'] = str(user_id)
            st.switch_page("pages/dashboard.py")  # Redirect to dashboard
        else:
            st.error("❌ Access Denied! Invalid username or password.")

if __name__ == "__main__":
    main()
