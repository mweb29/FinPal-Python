# user_auth_storage.py
import streamlit as st
import streamlit_authenticator as stauth
import json
import os
import pandas as pd
from streamlit_authenticator import Hasher
from typing import Dict, Any
from db_manager import save_user_data, load_user_data

CREDENTIALS_PATH = "user_data/credentials.json"

def load_credentials():
    with open(CREDENTIALS_PATH, "r") as f:
        return json.load(f)

def save_credentials(credentials):
    with open(CREDENTIALS_PATH, "w") as f:
        json.dump(credentials, f, indent=4)
        
credentials = load_credentials()

authenticator = stauth.Authenticate(
    credentials,
    "finpal_cookie", "random_signature", cookie_expiry_days=30
)

def login_user():
    for key in ["logout", "name", "authentication_status", "username"]:
        if key not in st.session_state:
            st.session_state[key] = None

    print("DEBUG: Full loaded credentials dict:")
    print(json.dumps(credentials, indent=2))  # show full structure
    
    name, auth_status, username = authenticator.login("Login", "main")

    print("DEBUG: Login result ->", f"auth_status: {auth_status}, username: {username}, name: {name}")

    if auth_status:
        st.session_state["authentication_status"] = True
        st.session_state["username"] = username
        st.session_state["name"] = name
    elif auth_status is False:
        st.error("Username/password is incorrect")
    elif auth_status is None:
        st.warning("Please enter your username and password")

    return username if auth_status else None

