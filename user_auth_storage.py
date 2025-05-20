# user_auth_storage.py
import streamlit as st
import streamlit_authenticator as stauth
import json
import os
import pandas as pd
from typing import Dict, Any
from db_manager import save_user_data, load_user_data

# --- CONFIGURATION ---
USER_DATA_DIR = "user_data"

# Example user credentials (hash these in production!)
names = ["Michael", "Test User", "Victoria"]
usernames = ["mweb", "test", "vcarl"]
passwords = ["123", "testpass", "7890"]

# --- HASH PASSWORDS ---
hashed_pw = stauth.Hasher(passwords).generate()
credentials = {
    "usernames": {
        u: {"name": n, "password": p}
        for u, n, p in zip(usernames, names, hashed_pw)
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "finpal_cookie", "random_signature", cookie_expiry_days=30
)

def login_user():
    if 'logout' not in st.session_state:
        st.session_state['logout'] = False

    name, auth_status, username = authenticator.login("Login", "main")

    if auth_status:
        st.session_state["authentication_status"] = True
        st.session_state["username"] = username
        save_user_data(username, load_user_data(username))  # Optional based on your design

    elif auth_status is False:
        st.error("Username/password is incorrect")
    elif auth_status is None:
        st.warning("Please enter your username and password")

    return username
