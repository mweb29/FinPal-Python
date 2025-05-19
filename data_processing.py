import pandas as pd

# Load normalized state tax brackets CSV once
STATE_BRACKETS_DF = pd.read_csv("normalized_state_brackets_2024.csv")

# Map non-standard state labels to standard two-letter codes
STATE_CODE_MAP = {
    "Ala": "AL", "Alaska": "AK", "Ariz": "AZ", "Ark": "AR", "Calif": "CA", "Colo": "CO",
    "Conn": "CT", "DC": "DC", "Del": "DE", "Fla": "FL", "Ga": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Ill": "IL", "Ind": "IN", "Iowa": "IA", "Kans": "KS", "Ky": "KY", "La": "LA", "Maine": "ME",
    "Md": "MD", "Mass": "MA", "Mich": "MI", "Minn": "MN", "Miss": "MS", "Mo": "MO", "Mont": "MT",
    "Neb": "NE", "Nev": "NV", "NH": "NH", "NJ": "NJ", "NM": "NM", "NY": "NY", "NC": "NC", "ND": "ND",
    "Ohio": "OH", "Okla": "OK", "Ore": "OR", "Pa": "PA", "RI": "RI", "SC": "SC", "SD": "SD",
    "Tenn": "TN", "Tex": "TX", "Utah": "UT", "Vt": "VT", "Va": "VA", "Wash": "WA", "W Va": "WV",
    "Wis": "WI", "Wyo": "WY"
}


def calculate_taxes(gross_income, state):
    """Calculates federal and state income taxes using progressive brackets."""
    # Federal tax brackets for single filers (2024)
    federal_brackets = [
        (0, 11000, 0.10),
        (11000, 44725, 0.12),
        (44725, 95375, 0.22),
        (95375, 182100, 0.24),
        (182100, 231250, 0.32),
        (231250, 578125, 0.35),
        (578125, float('inf'), 0.37)
    ]

    def apply_brackets(income, brackets):
        tax = 0.0
        for i, (lower, upper, rate) in enumerate(brackets):
            if income > lower:
                taxed_amount = min(income, upper) - lower
                tax += taxed_amount * rate
            else:
                break
        return tax

    # Map full name to standard code
    state_code = STATE_CODE_MAP.get(state, state)

    # Filter state brackets
    state_df = STATE_BRACKETS_DF[STATE_BRACKETS_DF["State"] == state_code.upper()]
    if state_df.empty:
        state_brackets = [(0, float('inf'), 0.04)]
    else:
        sorted_brackets = state_df.sort_values(by="Bracket_Min")
        rates = list(sorted_brackets["Rate"].values)
        thresholds = list(sorted_brackets["Bracket_Min"].values)
        state_brackets = []
        for i in range(len(rates)):
            lower = thresholds[i]
            upper = thresholds[i + 1] if i + 1 < len(thresholds) else float('inf')
            state_brackets.append((lower, upper, rates[i]))

    federal_tax = apply_brackets(gross_income, federal_brackets)
    state_tax = apply_brackets(gross_income, state_brackets)
    total_tax = federal_tax + state_tax
    net_income = gross_income - total_tax
    return net_income

def parse_bank_statement(file):
    """Assumes a simple CSV with at least columns: Date, Amount, Description."""
    try:
        df = pd.read_csv(file)
        df = df.rename(columns=lambda x: x.strip().lower())

        if 'date' not in df.columns or 'amount' not in df.columns:
            raise ValueError("CSV must contain 'Date' and 'Amount' columns")

        df['Category'] = df['description'].apply(categorize_expense)
        df = df.rename(columns={
            'date': 'Date',
            'amount': 'Amount',
            'description': 'Description'
        })
        df = df[['Date', 'Amount', 'Category', 'Description']]
        return df
    except Exception as e:
        raise ValueError(f"Failed to parse bank statement: {e}")

def categorize_expense(description):
    """Basic keyword matching to categorize expenses."""
    description = str(description).lower()
    if any(word in description for word in ['rent', 'apartment', 'lease']):
        return "Rent"
    elif any(word in description for word in ['grocery', 'supermarket', 'whole foods']):
        return "Groceries"
    elif any(word in description for word in ['uber', 'lyft', 'metro', 'gas']):
        return "Transportation"
    elif any(word in description for word in ['restaurant', 'cafe', 'mcdonald', 'chipotle']):
        return "Dining Out"
    elif any(word in description for word in ['netflix', 'spotify', 'subscription']):
        return "Subscriptions"
    elif any(word in description for word in ['insurance']):
        return "Insurance"
    elif any(word in description for word in ['entertainment', 'movie', 'theatre']):
        return "Entertainment"
    elif any(word in description for word in ['utility', 'electric', 'water', 'coned']):
        return "Utilities"
    else:
        return "Other"
