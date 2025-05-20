import streamlit as st
from utils.data_processing import calculate_taxes, categorize_expense, parse_bank_statement
from db_manager import init_db, load_user_data, save_user_data, initialize_session_from_user_data, persist_session
from user_auth_storage import login_user

st.set_page_config(page_title="FinPal Budget App", layout="wide")

# Initialize the database
init_db()

# Check if the user is authenticated
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None

# If the user is not authenticated, prompt for login
if st.session_state["authentication_status"] != True:
    username = login_user()
    st.stop()

# If the user is authenticated, proceed with loading user data
username = st.session_state["username"]
user_data = load_user_data(username)
initialize_session_from_user_data(user_data)

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
    st.session_state.annual_income = 0.0
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
    
    with st.form("budget_form"):
        income = st.number_input(
            "Enter your gross annual income ($):",
            min_value=0.0,
            value=st.session_state.annual_income
        )
        state = st.selectbox(
            "Select your state (for tax estimate):",
            US_STATE_CODES,
            index=US_STATE_CODES.index(st.session_state.selected_state)
        )
        nyc = False
        if state == "NY":
            nyc = st.checkbox(
                "Check this if you live in NYC (3.876% city tax applies)",
                value=st.session_state.nyc_resident
            )
        submitted = st.form_submit_button("Save and Estimate Taxes")

    if submitted:
        # Save inputs
        st.session_state.annual_income = income
        st.session_state.selected_state = state
        st.session_state.nyc_resident = nyc

        # Calculate and save taxes
        st.session_state.tax_details = calculate_taxes(
            gross_income=income,
            state=state,
            nyc=nyc
        )
        st.success("Tax estimate calculated and saved.")
        
    monthly_net_income = st.session_state["tax_details"]["net_income"] / 12
    st.session_state["tax_summary"] = st.session_state.tax_details

    st.subheader("Tax Breakdown")
    st.write(f"Standard Deduction: ${st.session_state["tax_details"]['standard_deduction']:,.2f}")
    st.write(f"Taxable Income: ${st.session_state["tax_details"]['taxable_income']:,.2f}")
    st.write(f"Federal Tax: ${st.session_state["tax_details"]['federal_tax']:,.2f}")
    st.write(f"State Tax: ${st.session_state["tax_details"]['state_tax']:,.2f}")
    if st.session_state.nyc_resident:
        st.write(f"NYC Tax: ${st.session_state["tax_details"]['nyc_tax']:,.2f}")
    st.write(f"Total Tax: ${st.session_state["tax_details"]['total_tax']:,.2f}")
    st.write(f"Net Monthly Income: ${monthly_net_income:,.2f}")
    
    # 🆕 Add this right below the tax numbers:
    if st.session_state["tax_details"]["federal_breakdown"]:
        federal_df = pd.DataFrame(st.session_state["tax_details"]["federal_breakdown"])
        federal_df = federal_df[["lower_bound", "upper_bound", "rate", "amount_taxed", "tax"]]
        federal_df.columns = ["From", "To", "Rate", "Amount Taxed", "Tax"]
        st.markdown("###### Federal Tax Breakdown")
        st.table(federal_df)
    else:
        st.markdown("###### Federal Tax Breakdown")
        st.info("Enter an income above $0 to view federal tax bracket breakdown.")

    if st.session_state["tax_details"]["state_breakdown"]:
        state_df = pd.DataFrame(st.session_state["tax_details"]["state_breakdown"])
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

    # Save
    if "budget" in st.session_state:
        persist_session(username)

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

    # Protect against missing keys
    budget = st.session_state.get("budget", {})
    expenses = st.session_state.get("expenses", pd.DataFrame())
    tax_summary = st.session_state.get("tax_summary", {})
    
    estimated_spend = sum(budget.values()) if budget else 0
    total_expenses = expenses["Amount"].sum() if not expenses.empty else 0
    monthly_net_income = tax_summary.get("net_income", 0) / 12
    expected_savings = monthly_net_income - estimated_spend
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Expected Monthly Income", f"${monthly_net_income:,.2f}")
        st.metric("Expected Monthly Savings", f"${expected_savings:,.2f}")
    with col2:
        st.metric("Estimated Spend (Budgeted Total):", f"${estimated_spend:,.2f}")
        st.metric("Total Monthly Expenses", f"${total_expenses:,.2f}")

    
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

    # Defining the stacking of the graph
    category_order = (
        stacked_df.groupby("Category")["Amount"]
        .sum()
        .sort_values(ascending=False)
        .index
        .tolist()
    )
    
    # Plot as a grouped, stacked bar chart by Type
    chart = alt.Chart(stacked_df).mark_bar().encode(
        x=alt.X('Type:N', title=None),  # 'Budgeted' and 'Actual'
        y=alt.Y('Amount:Q', stack='zero', title='Total Spending ($)'),
        color=alt.Color(
            'Category:N',
            title='Category',
            sort=category_order  # <- this is safe now
        ),
        tooltip=['Category:N', 'Amount:Q']
    ).properties(width=600, height=400)
        
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Detailed Expenses")
    st.dataframe(st.session_state.expenses)

    # Save
    if "budget" in st.session_state:
        persist_session(username)
