import streamlit as st
import pandas as pd
import os
import plotly.express as px
from utils.data_processing import calculate_taxes, categorize_expense, parse_bank_statement
from utils.gamification import calculate_points, get_achievements

st.set_page_config(page_title="FinPal Budget App", layout="wide")

st.sidebar.title("FinPal Setup")

# Multi-page setup
page = st.sidebar.radio("Navigate", ["Budget Setup", "Track Expenses"])

# Load full list of US states for dropdown
US_STATE_CODES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA',
    'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK',
    'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

# Session state initialization
if "annual_income" not in st.session_state:
    st.session_state.annual_income = 0
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date", "Amount", "Category", "Description"])
if "budget" not in st.session_state:
    st.session_state.budget = {}

if page == "Budget Setup":
    st.title("Budget Setup")

    st.session_state.annual_income = st.number_input("Enter your gross annual income ($):", min_value=0)

    state = st.selectbox("Select your state (for tax estimate):", US_STATE_CODES)
    nyc_resident = False
    if state == "NY":
        nyc_resident = st.checkbox("Check this if you live in NYC (3.876% city tax applies)")

    tax_details = calculate_taxes(st.session_state.annual_income, state, nyc=nyc_resident)
    monthly_net_income = tax_details["net_income"] / 12
    st.session_state["tax_summary"] = tax_details

    st.subheader("Tax Breakdown")
    st.write(f"Standard Deduction: ${tax_details['standard_deduction']:,.2f}")
    st.write(f"Taxable Income: ${tax_details['taxable_income']:,.2f}")
    st.write(f"Federal Tax: ${tax_details['federal_tax']:,.2f}")
    st.write(f"State Tax: ${tax_details['state_tax']:,.2f}")
    if nyc_resident:
        st.write(f"NYC Tax: ${tax_details['nyc_tax']:,.2f}")
    st.write(f"Total Tax: ${tax_details['total_tax']:,.2f}")
    st.write(f"Net Monthly Income: ${monthly_net_income:,.2f}")
    
    # 🆕 Add this right below the tax numbers:
    if tax_details["federal_breakdown"]:
        federal_df = pd.DataFrame(tax_details["federal_breakdown"])
        federal_df = federal_df[["lower_bound", "upper_bound", "rate", "amount_taxed", "tax"]]
        federal_df.columns = ["From", "To", "Rate", "Amount Taxed", "Tax"]
        st.markdown("###### Federal Tax Breakdown")
        st.table(federal_df)
    else:
        st.markdown("#### Federal Tax Breakdown")
        st.info("Enter an income above $0 to view federal tax bracket breakdown.")

    st.subheader("Set Monthly Budget Goals")
    # Only define categories once
    if "budget" not in st.session_state:
        st.session_state.budget = {}
    
    categories = ["Rent", "Groceries", "Dining Out", "Transportation", "Entertainment", "Utilities", "Insurance", "Subscriptions", "Other"]
    
    # Set each category only if it's not already present
    for cat in categories:
        if cat not in st.session_state.budget:
            st.session_state.budget[cat] = 0
    
    # Then create input boxes without overwriting stored values
    for cat in categories:
        st.session_state.budget[cat] = st.number_input(
            f"{cat} Budget ($)", min_value=0, value=st.session_state.budget[cat], step=50
        )

elif page == "Track Expenses":
    st.title("Track Expenses & Upload Statements")

    st.header("Add a New Expense")
    with st.form("expense_form"):
        date = st.date_input("Date")
        amount = st.number_input("Amount ($)", min_value=0.0, format="%.2f")
        category = st.selectbox("Category", list(st.session_state.budget.keys()))
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
    monthly_net_income = st.session_state.tax_summary["net_income"] / 12
    savings = monthly_net_income - total_expenses

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

    st.markdown("---")
    st.markdown("💡 **Tip:** The more detailed your descriptions and the closer you stay to your budget, the more points you'll earn!")
