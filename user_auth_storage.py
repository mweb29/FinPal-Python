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
    # Safely initialize expected session keys
    for key in ["logout", "name", "authentication_status", "username"]:
        if key not in st.session_state:
            st.session_state[key] = None

    # Perform login
    name, auth_status, username = authenticator.login("Login", "main")

    # Save session state after login
    if auth_status:
        st.session_state["authentication_status"] = True
        st.session_state["username"] = username
        st.session_state["name"] = name  # <- This line ensures 'name' is preserved
    elif auth_status is False:
        st.error("Username/password is incorrect")
    elif auth_status is None:
        st.warning("Please enter your username and password")

    return username

