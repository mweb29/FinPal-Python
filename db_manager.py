
import sqlite3
import os
import json
import pandas as pd
from typing import Dict, Any

DB_PATH = "user_data/finpal_users.db"

# --- INIT DB ---
def init_db():
    os.makedirs("user_data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Store metadata like budget, income, state, NYC flag
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            annual_income REAL,
            selected_state TEXT,
            nyc_resident INTEGER,
            budget TEXT,
            tax_summary TEXT
        )
    ''')

    # Store expenses in a separate table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            username TEXT,
            date TEXT,
            amount REAL,
            category TEXT,
            description TEXT
        )
    ''')

    conn.commit()
    conn.close()

# --- SAVE USER DATA ---
def save_user_data(username: str, data: Dict[str, Any]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Convert complex objects
    budget_json = json.dumps(data.get("budget", {}))
    tax_summary_json = json.dumps(data.get("tax_summary", {}))

    # Upsert user metadata
    cursor.execute('''
        INSERT INTO users (username, annual_income, selected_state, nyc_resident, budget, tax_summary)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            annual_income=excluded.annual_income,
            selected_state=excluded.selected_state,
            nyc_resident=excluded.nyc_resident,
            budget=excluded.budget,
            tax_summary=excluded.tax_summary
    ''', (
        username,
        data.get("income", 0),
        data.get("state", "NY"),
        int(data.get("nyc_resident", False)),
        budget_json,
        tax_summary_json
    ))

    # Delete and re-insert all expenses for user
    cursor.execute("DELETE FROM expenses WHERE username = ?", (username,))
    for _, row in pd.DataFrame(data.get("expenses", {})).iterrows():
        cursor.execute("""
            INSERT INTO expenses (username, date, amount, category, description)
            VALUES (?, ?, ?, ?, ?)
        """, (username, str(row["Date"]), row["Amount"], row["Category"], row["Description"]))

    conn.commit()
    conn.close()

# --- LOAD USER DATA ---
def load_user_data(username: str) -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Load metadata
    cursor.execute("SELECT annual_income, selected_state, nyc_resident, budget, tax_summary FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {}

    annual_income, selected_state, nyc_resident, budget_json, tax_summary_json = row

    # Load expenses
    cursor.execute("SELECT date, amount, category, description FROM expenses WHERE username = ?", (username,))
    expenses = cursor.fetchall()
    conn.close()

    expenses_df = pd.DataFrame(expenses, columns=["Date", "Amount", "Category", "Description"])

    return {
        "income": annual_income,
        "state": selected_state,
        "nyc_resident": bool(nyc_resident),
        "budget": json.loads(budget_json),
        "tax_summary": json.loads(tax_summary_json),
        "expenses": expenses_df.to_dict(orient="list")
    }
