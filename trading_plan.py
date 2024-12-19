import streamlit as st
from datetime import datetime
import requests
import json
import os
from math import floor
from dotenv import load_dotenv
import yfinance as yf
from pyfinsights.yfinance import get_earnings_dates, get_dividends_date
from pyfinsights.utils import get_earnings_date_from_df

load_dotenv()

# Create a title for the app
st.title("Trading Plan - Stocks")

notion_api_key = os.getenv("NOTION_API_KEY")
notion_db_id = os.getenv("NOTION_DB_ID")

# API endpoint for creating a new page in a database
url = "https://api.notion.com/v1/pages"

# Set up the headers for the API request
headers = {
    "Authorization": f"Bearer {notion_api_key}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def calculate_trade_size(
    entry_price,
    stop_loss,
    account_balance,
    risk_per_trade_percent,
    risked_capital_percent,
):
    try:
        risk_per_trade = (risk_per_trade_percent / 100) * account_balance
        quantity = risk_per_trade / (entry_price - stop_loss)
        risked_capital_per_trade = (risked_capital_percent / 100) * account_balance
        if quantity * entry_price > risked_capital_per_trade:
            quantity = floor(risked_capital_per_trade / entry_price)
        return quantity
    except:
        return 0,0


# Caching the result of expensive_computation / data access using @st.cache_data
@st.cache_data
def get_earnings_dates_cached(ticker_symbol):
    return get_earnings_dates(ticker_symbol)


global company_name

# Sidebar inputs
st.sidebar.header("Trading Parameters")

# Account balance input with default value
account_balance = st.sidebar.number_input(
    "Account Balance ($)", value=100000.0, step=100.0, min_value=0.0
)

# Risk per trade (0.5% of account balance)
risk_per_trade_percent = st.sidebar.number_input(
    "Risk per Trade (% of Account Balance)",
    value=0.5,
    step=0.1,
    min_value=0.0,
    max_value=100.0,
)
risk_per_trade = (risk_per_trade_percent / 100) * account_balance

# Risked capital per trade (10% of account balance)
risked_capital_percent = st.sidebar.number_input(
    "Risked Capital per Trade (% of Account Balance)",
    value=10.0,
    step=1.0,
    min_value=0.0,
    max_value=100.0,
)
risked_capital_per_trade = (risked_capital_percent / 100) * account_balance

# Displaying values in main app
st.write(f"### Account Balance: ${account_balance:,.2f}")
st.write(f"Risk per Trade (0.5%): ${risk_per_trade:,.2f}")
st.write(f"Risked Capital per Trade (10%): ${risked_capital_per_trade:,.2f}")

# Create a form in Streamlit
# with st.form(key="trading_plan_form"):
ticker_symbol = st.text_input("Ticker-Symbol (Ticker Symbol)", "AAPL")

try:
    ticker = yf.Ticker(ticker_symbol)
    company_name = str(ticker.info["shortName"])
    st.write(company_name)
except:
    pass  # TODO catch the exception

earnings_df = get_earnings_dates_cached(ticker_symbol)
earnings_date, earnings_date_confirmed_retrieved = get_earnings_date_from_df(
    earnings_df, ticker_symbol
)
pays_dividends, dividends_date_retrieved, ex_dividend_date, ticker = get_dividends_date(
    ticker_symbol
)

stock = st.text_input("Aktie (Stock)", value=company_name)

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Datum (Date)", value=datetime.today())

    with col2:
        time = st.time_input("Uhrzeit (Time)", value=datetime.now().time())

with st.container(border=True):
    # st.text("Preis")
    col1, col2 = st.columns(2)

    with col1:
        entry_price = st.number_input(
            "Preis (Entry Price)", min_value=0.0, format="%.2f"
        )

    with col2:
        order_type = st.radio(
            "Order Type", ["LMT", "MKT", "STP/STP LMT"], horizontal=True
        )


# Initialize session state to preserve 'quantity' between reruns
if "quantity" not in st.session_state:
    st.session_state["quantity"] = 1  # Default quantity


with st.container(border=True):

    col1, col2 = st.columns(2)
    with col1:
        initial_stop = st.number_input(
            "Initialer Stop (Initial Stop)", min_value=0.0, format="%.2f"
        )

    with col2:
        calculate_quantity = st.button(label="Calculate quantity")
        pass

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        if calculate_quantity:
            st.session_state["quantity"] = calculate_trade_size(
                entry_price,
                initial_stop,
                account_balance,
                risk_per_trade_percent,
                risked_capital_percent,
            )

        quantity = st.number_input(
            "Menge (Quantity)", value=st.session_state["quantity"])#, min_value=0.0, max_value=10000.0, step=1.0)
        st.session_state["quantity"] = quantity
    with col2:
        action = st.radio("Aktion", options=["Long", "Short"], horizontal=True)

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        exchange = st.text_input("Börse (Exchange)", "SMART")
    with col2:

        validity = st.radio(
            "Gültigkeit (Order Validity)",
            ["DAY", "GTC (Good Till Cancelled)"],
            horizontal=True,
        )
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        earnings_date = st.date_input("Earnings Datum (Earnings Date)", earnings_date)
    with col2:
        confirmation_index = 1 if earnings_date_confirmed_retrieved == True else 0
        earnings_date_confirmed = st.radio(
            "Earnings Datum bestätigt (Earnings Date Confirmed)",
            ["Nein", "Ja"],
            index=confirmation_index,
            horizontal=True,
        )

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:

        dividends = st.number_input(
            "Dividenden (Dividends)", min_value=0.0, format="%.2f"
        )
    with col2:
        if pays_dividends == False:
            dividends_date = st.date_input(
                "Dividenden Datum (Dividends Date)",
                None,
            )
        else:
            dividends_date = st.date_input(
                "Ex-Dividenden Datum (Dividends Date)",
                dividends_date_retrieved,
            )

with st.container(border=True):
    st.text("Drei wichtige Fragen vor jedem Trade")
    reason = st.text_area(
        "Warum eröffne ich die Position? (Reason for opening the position)"
    )
    trade_management_plan = st.text_area(
        "Wie manage ich den Trade? (Trade Management Plan)"
    )

    plan_b = st.text_area("Was ist mein Plan B? (Plan B - Exit Scenario, Stop)")

# Add a submit button
submit_button = st.button(label="Save")
save_to_notion_button = st.button(label="Save to Notion")

# Process the form data
if submit_button:
    st.write("Form Submitted!")
    st.write("Reason for opening the position:", reason)
    st.write("Date:", date)
    st.write("Time:", time)
    st.write("Action:", action)
    st.write("Stock:", company_name)
    st.write("Ticker Symbol:", ticker_symbol)
    st.write("Entry Price:", entry_price)
    st.write("Order Validity:", validity)
    st.write("Exchange:", exchange)
    # st.write("Long/Short:", long_short)
    st.write("Quantity:", quantity)
    st.write("Earnings Date:", earnings_date)
    st.write("Dividends:", dividends)
    st.write("Trade Management Plan:", trade_management_plan)
    # st.write("Date for Management Plan:", date_management)
    # st.write("Amount:", amount_management)
    st.write("Plan B (Exit Scenario, Stop):", plan_b)

if save_to_notion_button:
    # The data for the new entry

    # Map the string response to a boolean
    earnings_date_confirmed_bool = True if earnings_date_confirmed == "Ja" else False

    new_page_data = {
        "parent": {"database_id": notion_db_id},
        "properties": {
            "Symbol": {"title": [{"text": {"content": ticker_symbol}}]},
            # "Description": {
            #     "rich_text": [{"text": {"content": "This is an example description."}}]
            # },
            "Action": {"select": {"name": "Long"}},
            "Date": {
                "date": {"start": date.isoformat()}
            },  # ISO 8601 formatted date with time
            "Quantity": {"number": quantity},  # Quantity as a number
            "Entry Price": {"number": entry_price},
            "Initial Stop": {"number": initial_stop},
            "Current Stop": {"number": initial_stop},
            "Order Validity": {"select": {"name": validity}},
            "Order Type": {"select": {"name": order_type}},
            "Earnings Date": {
                "date": {"start": earnings_date.isoformat()}
            },  # ISO 8601 formatted date with time
            # "Dividends Date": {"date": {"start": dividends_date.isoformat()}},
            "Dividends": {"number": dividends},
            "Stock": {
                "rich_text": [{"text": {"content": stock}}]
            },  # Text for stock status
            "Trade Management": {
                "rich_text": [{"text": {"content": trade_management_plan}}]
            },
            "Reason": {"rich_text": [{"text": {"content": reason}}]},
            "Plan B": {"rich_text": [{"text": {"content": plan_b}}]},
            "Earnings Date Confirmed": {"checkbox": earnings_date_confirmed_bool},
        },
    }

    # Conditionally add Dividends Date if it's not None
    if dividends_date is not None:
        new_page_data["properties"]["Dividends Date"] = {
            "date": {"start": dividends_date.isoformat()}
        }

    # Make the request
    response = requests.post(url, headers=headers, data=json.dumps(new_page_data))

    # Check the response
    if response.status_code == 200:
        st.write("Trade info has been saved to Notion")
    else:
        st.write("Failed to create a page. Response:", response.json())
