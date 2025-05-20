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
names = ["Michael", "Test User"]
usernames = ["mweb", "test"]
passwords = ["123", "testpass"]

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
    for key in ["authentication_status", "username", "name"]:
        if key not in st.session_state:
            st.session_state[key] = None

    name, auth_status, username = authenticator.login("Login", "main")

    if auth_status:
        authenticator.logout("Logout", "sidebar")
        st.sidebar.success(f"Welcome {name}")
        return username
    elif auth_status is False:
        st.error("Incorrect username or password.")
        st.stop()
    else:
        st.warning("Please enter your credentials.")
        st.stop()
