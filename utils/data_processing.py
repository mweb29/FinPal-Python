import pandas as pd

STATE_BRACKETS_DF = pd.read_csv("normalized_state_brackets_2024.csv")
# Standardize state names by removing periods, trimming spaces, and converting to uppercase for reliable matching
STATE_BRACKETS_DF["State"] = STATE_BRACKETS_DF["State"].str.replace(".", "", regex=False).str.strip().str.upper()

# Reversed map: full uppercase names like N D to their USPS codes
STATE_NAME_TO_CODE = {
    "ALA": "AL", "ALASKA": "AK", "ARIZ": "AZ", "ARK": "AR", "CALIF": "CA", "COLO": "CO",
    "CONN": "CT", "DC": "DC", "DEL": "DE", "FLA": "FL", "GA": "GA", "HAWAII": "HI", "IDAHO": "ID",
    "ILL": "IL", "IND": "IN", "IOWA": "IA", "KANS": "KS", "KY": "KY", "LA": "LA", "MAINE": "ME",
    "MD": "MD", "MASS": "MA", "MICH": "MI", "MINN": "MN", "MISS": "MS", "MO": "MO", "MONT": "MT",
    "NEB": "NE", "NEV": "NV", "NH": "NH", "NJ": "NJ", "NM": "NM", "NY": "NY", "NC": "NC", "ND": "ND",
    "OHIO": "OH", "OKLA": "OK", "ORE": "OR", "PA": "PA", "RI": "RI", "SC": "SC", "SD": "SD",
    "TENN": "TN", "TEX": "TX", "UTAH": "UT", "VT": "VT", "VA": "VA", "WASH": "WA", "W VA": "WV",
    "WIS": "WI", "WYO": "WY"
}


def calculate_taxes(gross_income, state, nyc=False):
    """Calculates federal, state, and NYC taxes and returns detailed breakdown."""
    # These are the 2024 U.S. federal tax brackets for single filers
    federal_brackets = [
        (0, 11000, 0.10), (11000, 44725, 0.12), (44725, 95375, 0.22),
        (95375, 182100, 0.24), (182100, 231250, 0.32),
        (231250, 578125, 0.35), (578125, float('inf'), 0.37)
    ]

    def apply_brackets(income, brackets):
        tax = 0.0
        for lower, upper, rate in brackets:
            if income > lower:
                taxed = min(income, upper) - lower
                tax += taxed * rate
            else:
                break
        return tax

    state_clean = state.upper().strip()
    # Reverse the mapping so we can go from USPS code (e.g., 'NY') back to the normalized format used in the CSV (e.g., 'NEW YORK')
    reverse_lookup = {v: k for k, v in STATE_NAME_TO_CODE.items()}
    state_lookup = reverse_lookup.get(state_clean, state_clean)

    state_df = STATE_BRACKETS_DF[STATE_BRACKETS_DF["State"] == state_lookup]

    # Use default flat tax bracket if state is not found
    if state_df.empty:
        state_brackets = [(0, float('inf'), 0.04)]
    else:
        sorted_df = state_df.sort_values("Bracket_Min")
        thresholds = sorted_df["Bracket_Min"].tolist()
        rates = sorted_df["Rate"].tolist()
        state_brackets = [
            (thresholds[i], thresholds[i+1] if i+1 < len(thresholds) else float('inf'), rates[i])
            for i in range(len(rates))
        ]

    federal_tax = apply_brackets(gross_income, federal_brackets)
    state_tax = apply_brackets(gross_income, state_brackets)
    # Add NYC tax if applicable
    nyc_tax = gross_income * 0.03876 if nyc and state_clean == "NY" else 0.0

    total_tax = federal_tax + state_tax + nyc_tax
    net_income = gross_income - total_tax

    return {
        "net_income": net_income,
        "federal_tax": federal_tax,
        "state_tax": state_tax,
        "nyc_tax": nyc_tax,
        "total_tax": total_tax
    }


def parse_bank_statement(file):
    try:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip().str.lower()
        if 'date' not in df or 'amount' not in df:
            raise ValueError("CSV must contain 'Date' and 'Amount'")
        df['Category'] = df['description'].apply(categorize_expense)
        return df.rename(columns={
            'date': 'Date', 'amount': 'Amount', 'description': 'Description'
        })[["Date", "Amount", "Category", "Description"]]
    except Exception as e:
        raise ValueError(f"Failed to parse bank statement: {e}")


def categorize_expense(description):
    description = str(description).lower()
    if any(x in description for x in ['rent', 'apartment', 'lease']): return "Rent"
    if any(x in description for x in ['grocery', 'whole foods', 'supermarket']): return "Groceries"
    if any(x in description for x in ['uber', 'lyft', 'metro', 'transit', 'gas']): return "Transportation"
    if any(x in description for x in ['restaurant', 'cafe', 'chipotle', 'mcdonald']): return "Dining Out"
    if any(x in description for x in ['netflix', 'spotify', 'subscription']): return "Subscriptions"
    if any(x in description for x in ['insurance']): return "Insurance"
    if any(x in description for x in ['entertainment', 'movie', 'concert']): return "Entertainment"
    if any(x in description for x in ['electric', 'water', 'coned', 'utility']): return "Utilities"
    return "Other"
