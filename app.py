import streamlit as st
import pandas as pd
import os
import altair as alt
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
if "selected_state" not in st.session_state:
    st.session_state.selected_state = "NY"
if "nyc_resident" not in st.session_state:
    st.session_state.nyc_resident = False

if page == "Budget Setup":
    st.title("Budget Setup")

    st.session_state.annual_income = st.number_input(
    "Enter your gross annual income ($):", min_value=0, value=st.session_state.annual_income
    )
    st.session_state.selected_state = st.selectbox(
        "Select your state (for tax estimate):", US_STATE_CODES, index=US_STATE_CODES.index(st.session_state.selected_state)
    )
    if st.session_state.selected_state == "NY":
        st.session_state.nyc_resident = st.checkbox(
            "Check this if you live in NYC (3.876% city tax applies)",
            value=st.session_state.nyc_resident
        )
    else:
        st.session_state.nyc_resident = False

    tax_details = calculate_taxes(
        gross_income=st.session_state.annual_income,
        state=st.session_state.selected_state,
        nyc=st.session_state.nyc_resident
    )
    monthly_net_income = tax_details["net_income"] / 12
    st.session_state["tax_summary"] = tax_details

    st.subheader("Tax Breakdown")
    st.write(f"Standard Deduction: ${tax_details['standard_deduction']:,.2f}")
    st.write(f"Taxable Income: ${tax_details['taxable_income']:,.2f}")
    st.write(f"Federal Tax: ${tax_details['federal_tax']:,.2f}")
    st.write(f"State Tax: ${tax_details['state_tax']:,.2f}")
    if st.session_state.nyc_resident:
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
        st.markdown("###### Federal Tax Breakdown")
        st.info("Enter an income above $0 to view federal tax bracket breakdown.")

    if tax_details["state_breakdown"]:
        state_df = pd.DataFrame(tax_details["state_breakdown"])
        state_df = state_df[["lower_bound", "upper_bound", "rate", "amount_taxed", "tax"]]
        state_df.columns = ["From", "To", "Rate", "Amount Taxed", "Tax"]
        st.markdown("###### State Tax Breakdown")
        st.table(state_df)
    else:
        st.markdown("###### State Tax Breakdown")
        st.info("Enter an income above $0 to view state tax bracket breakdown.")


    st.subheader("Set Monthly Budget Goals")
    # Only define categories once
    if "budget" not in st.session_state:
        st.session_state.budget = {}
    
    categories = ["Rent", "Groceries", "Transportation", "Entertainment", "Utilities", "Gym", "Internet"]
    
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

    ### Working on
    
    st.subheader("Spending by Category vs Budget")
    # Create DataFrame from session state
    budget_df = pd.DataFrame({
        "Category": list(st.session_state.budget.keys()),
        "Budgeted": list(st.session_state.budget.values())
    })
    
    # Create actuals DataFrame from expenses
    if not st.session_state.expenses.empty:
        actual_df = (
            st.session_state.expenses
            .groupby("Category")["Amount"]
            .sum()
            .reset_index()
            .rename(columns={"Amount": "Actual"})
        )
    else:
        actual_df = pd.DataFrame(columns=["Category", "Actual"])
    
    # Merge budget and actual
    combined_df = pd.merge(budget_df, actual_df, on="Category", how="outer").fillna(0)
    
    # Melt for two stacks: Budgeted and Actual
    stacked_budget = combined_df[["Category", "Budgeted"]].copy()
    stacked_budget["Type"] = "Budgeted"
    stacked_budget = stacked_budget.rename(columns={"Budgeted": "Amount"})
    
    stacked_actual = combined_df[["Category", "Actual"]].copy()
    stacked_actual["Type"] = "Actual"
    stacked_actual = stacked_actual.rename(columns={"Actual": "Amount"})
    
    # Combine into one long dataframe
    stacked_df = pd.concat([stacked_budget, stacked_actual])
    
    # Plot as a grouped, stacked bar chart by Type
    chart = alt.Chart(stacked_df).mark_bar().encode(
        x=alt.X('Type:N', title=None),  # One bar for Budgeted, one for Actual
        y=alt.Y('Amount:Q', stack='zero', title='Total Spending ($)'),
        color=alt.Color('Category:N', title='Category', scale=alt.Scale(scheme='category20')),
        tooltip=['Category:N', 'Amount:Q']
    ).properties(
        title="Stacked Budget vs Actual Spending",
        width=600,
        height=400
    )
    
    st.altair_chart(chart, use_container_width=True)



    st.subheader("Detailed Expenses")
    st.dataframe(st.session_state.expenses)


    ###
    
    # Gamification
    points = calculate_points(st.session_state.expenses, st.session_state.budget)
    achievements = get_achievements(points)

    st.sidebar.header("Gamification")
    st.sidebar.metric("Points", points)
    for a in achievements:
        st.sidebar.write(f"🏆 {a}")

    st.markdown("---")
    st.markdown("💡 **Tip:** The more detailed your descriptions and the closer you stay to your budget, the more points you'll earn!")
