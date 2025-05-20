# user_auth_storage.py
import streamlit as st
import streamlit_authenticator as stauth
import json
import os
import pandas as pd
from typing import Dict, Any

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

# --- SAVE DATA ---
def save_user_data(username: str, data: Dict[str, Any]):
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    filepath = os.path.join(USER_DATA_DIR, f"{username}.json")
    with open(filepath, "w") as f:
        json.dump(data, f)

# --- LOAD DATA ---
def load_user_data(username: str) -> Dict[str, Any]:
    filepath = os.path.join(USER_DATA_DIR, f"{username}.json")
    if os.path.exists(filepath):
        with open(filepath) as f:
            return json.load(f)
    return {}

# --- INITIALIZE SESSION STATE ---
def initialize_session_from_user_data(user_data: Dict[str, Any]):
    st.session_state.budget = user_data.get("budget", {})
    st.session_state.annual_income = user_data.get("income", 0)
    st.session_state.selected_state = user_data.get("state", "NY")
    expenses_dict = user_data.get("expenses", {})
    st.session_state.expenses = pd.DataFrame(expenses_dict) if expenses_dict else pd.DataFrame(columns=["Date", "Amount", "Category", "Description"])
    st.session_state.nyc_resident = user_data.get("nyc_resident", False)
    st.session_state.tax_summary = user_data.get("tax_summary", {})

# --- SAVE STATE ---
def persist_session(username: str):
    save_user_data(username, {
        "budget": st.session_state.budget,
        "income": st.session_state.annual_income,
        "state": st.session_state.selected_state,
        "expenses": st.session_state.expenses.to_dict(),
        "nyc_resident": st.session_state.nyc_resident,
        "tax_summary": st.session_state.get("tax_summary", {})
    })
