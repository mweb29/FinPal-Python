import streamlit as st
import json
from streamlit_authenticator import Hasher

CREDENTIALS_PATH = "user_data/credentials.json"

st.set_page_config(page_title="Admin - User Manager", layout="centered")
st.title("🔐 Admin: Add or Update a User")

# Form to input new user
with st.form("add_user_form"):
    new_username = st.text_input("New Username")
    new_name = st.text_input("Full Name")
    new_password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Save User")

# Handle form submission
if submitted:
    if not new_username or not new_name or not new_password:
        st.error("Please fill in all fields.")
    else:
        try:
            with open(CREDENTIALS_PATH, "r") as f:
                credentials = json.load(f)
        except FileNotFoundError:
            credentials = {"usernames": {}}

        # Hash password using streamlit_authenticator
        hashed_pw = Hasher([new_password]).generate()[0]

        # Add or overwrite user
        credentials["usernames"][new_username] = {
            "name": new_name,
            "password": hashed_pw
        }

        # Save back to file
        with open(CREDENTIALS_PATH, "w") as f:
            json.dump(credentials, f, indent=4)

        st.success(f"✅ User `{new_username}` added or updated successfully!")
