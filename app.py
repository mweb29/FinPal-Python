import streamlit as st
import pandas as pd
import os
from utils.data_processing import calculate_taxes, categorize_expense, parse_bank_statement
from utils.gamification import calculate_points, get_achievements
import plotly.express as px

st.set_page_config(page_title="FinPal Budget App", layout="wide")

st.title("FinPal - Gamified Budget Tracker")

# Initialize session state variables if not already set
if "income" not in st.session_state:
    st.session_state.income = 0
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date", "Amount", "Category", "Description"])
if "budget" not in st.session_state:
    st.session_state.budget = {}

st.sidebar.header("Monthly Income & Budget")
st.session_state.income = st.sidebar.number_input("Enter your gross monthly income ($):", min_value=0)

state = st.sidebar.selectbox("Select your state (for tax estimate):", ["NY", "CA", "TX", "FL", "MA", "Other"])
net_income = calculate_taxes(st.session_state.income, state)
st.sidebar.markdown(f"**Estimated Net Income:** ${net_income:,.2f}")

st.sidebar.subheader("Set Monthly Budget Goals")
categories = ["Rent", "Groceries", "Dining Out", "Transportation", "Entertainment", "Utilities", "Insurance", "Subscriptions", "Other"]
for cat in categories:
    st.session_state.budget[cat] = st.sidebar.number_input(f"{cat} Budget ($)", min_value=0, value=0, step=50)

st.header("Add a New Expense")
with st.form("expense_form"):
    date = st.date_input("Date")
    amount = st.number_input("Amount ($)", min_value=0.0, format="%.2f")
    category = st.selectbox("Category", categories)
    description = st.text_input("Description (optional)")
    submitted = st.form_submit_button("Add Expense")

if submitted:
    new_expense = pd.DataFrame([[date, amount, category, description]], columns=st.session_state.expenses.columns)
    st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)
    st.success("Expense added!")

st.header("Upload Bank Statement")
uploaded_file = st.file_uploader("Upload a CSV bank statement", type=["csv"])
if uploaded_file is not None:
    parsed_expenses = parse_bank_statement(uploaded_file)
    st.session_state.expenses = pd.concat([st.session_state.expenses, parsed_expenses], ignore_index=True)
    st.success("Bank statement parsed and expenses added!")

st.header("Expense Summary")
total_expenses = st.session_state.expenses["Amount"].sum()
savings = net_income - total_expenses

st.metric("Total Monthly Expenses", f"${total_expenses:,.2f}")
st.metric("Estimated Monthly Savings", f"${savings:,.2f}")

category_summary = st.session_state.expenses.groupby("Category")["Amount"].sum().reset_index()
st.subheader("Spending by Category vs Budget")
category_summary["Budget"] = category_summary["Category"].apply(lambda x: st.session_state.budget.get(x, 0))
category_summary["Over Budget"] = category_summary["Amount"] > category_summary["Budget"]

fig_bar = px.bar(category_summary, x="Category", y=["Amount", "Budget"], barmode="group", title="Actual vs Budgeted Spending")
st.plotly_chart(fig_bar, use_container_width=True)

fig_pie = px.pie(category_summary, names="Category", values="Amount", title="Current Month's Expense Distribution")
st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("Detailed Expenses")
st.dataframe(st.session_state.expenses)

# Gamification
points = calculate_points(st.session_state.expenses, st.session_state.budget)
achievements = get_achievements(points)

st.sidebar.header("Gamification")
st.sidebar.metric("Points", points)
for a in achievements:
    st.sidebar.write(f"🏆 {a}")

# Add user feedback encouragement
st.markdown("---")
st.markdown("💡 **Tip:** The more detailed your descriptions and the closer you stay to your budget, the more points you'll earn!")
