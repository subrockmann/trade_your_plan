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


def calculate_position_size(
    entry_price,
    stop_loss,
    account_balance,
    risk_per_trade_percent=0.5,
    risked_capital_percent=10.0,
):
    """
    Calculate the trade size (quantity) based on risk management parameters.

    Parameters:
        entry_price (float): The price at which the trade is entered.
        stop_loss (float): The stop loss price for the trade.
        account_balance (float): The total account balance.
        risk_per_trade_percent (float): The percentage of account balance to risk per trade.
        risked_capital_percent (float): The maximum percentage of account balance to allocate to the trade.

    Returns:
        int: The calculated quantity of shares to trade.
    """
    try:
        # Calculate the dollar amount to risk per trade
        risk_per_trade = (risk_per_trade_percent / 100) * account_balance

        # Calculate the quantity based on risk per trade and the difference between entry price and stop loss
        quantity = risk_per_trade / (entry_price - stop_loss)

        # Calculate the maximum capital to allocate to the trade
        max_capitial_per_trade = (risked_capital_percent / 100) * account_balance

        # Adjust quantity if the total cost exceeds the allowed capital allocation
        if quantity * entry_price > max_capitial_per_trade:
            quantity = floor(max_capitial_per_trade / entry_price)

        # Ensure the quantity is always positive
        quantity = floor(abs(quantity))
        return quantity
    except ZeroDivisionError:
        # Handle division by zero if entry_price equals stop_loss
        return 0
    except Exception as e:
        # Log or handle other unexpected exceptions
        return 0


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
max_capitial_per_trade = (risked_capital_percent / 100) * account_balance

# Displaying values in main app
st.write(f"### Account Balance: ${account_balance:,.2f}")
st.write(f"Risk per Trade (0.5%): ${risk_per_trade:,.2f}")
st.write(f"Risked Capital per Trade (10%): ${max_capitial_per_trade:,.2f}")

# Create a form in Streamlit
# with st.form(key="trading_plan_form"):
ticker_symbol = st.text_input("Ticker-Symbol (Ticker Symbol)", "")

# Initialize session state variables for all input fields
if 'previous_ticker_symbol' not in st.session_state:
    st.session_state['previous_ticker_symbol'] = ""
if 'entry_price' not in st.session_state:
    st.session_state['entry_price'] = 0.0
if 'initial_stop' not in st.session_state:
    st.session_state['initial_stop'] = 0.0
if 'quantity' not in st.session_state:
    st.session_state['quantity'] = 0
if 'stock' not in st.session_state:
    st.session_state['stock'] = ""
if 'action' not in st.session_state:
    st.session_state['action'] = ""
if 'reason' not in st.session_state:
    st.session_state['reason'] = ""
if 'trade_management_plan' not in st.session_state:
    st.session_state['trade_management_plan'] = ""
if 'plan_b' not in st.session_state:
    st.session_state['plan_b'] = ""

# Clear all input fields if a new symbol is chosen
if ticker_symbol != st.session_state['previous_ticker_symbol']:
    st.session_state['previous_ticker_symbol'] = ticker_symbol
    st.session_state['entry_price'] = 0.0
    st.session_state['initial_stop'] = 0.0
    st.session_state['quantity'] = 0
    st.session_state['stock'] = ""
    st.session_state['action'] = ""
    st.session_state['reason'] = ""
    st.session_state['trade_management_plan'] = ""
    st.session_state['plan_b'] = ""

if ticker_symbol:  # Only proceed if a ticker symbol is provided
    try:
        ticker = yf.Ticker(ticker_symbol)
        company_name = str(ticker.info.get("shortName", ""))
        st.write(company_name)

        # Fetch earnings and dividends data
        earnings_df = get_earnings_dates_cached(ticker_symbol)
        earnings_date, earnings_date_confirmed_retrieved = get_earnings_date_from_df(
            earnings_df, ticker_symbol
        )
        pays_dividends, dividends_date_retrieved, ex_dividend_date, ticker = get_dividends_date(
            ticker_symbol
        )

        # Removed redundant 'value' parameter for widgets with 'key' to avoid warnings
        stock = st.text_input("Aktie (Stock)", key="stock")
    except Exception as e:
        st.write("Error fetching data for the ticker symbol. Please check the input.")
        company_name = ""
        earnings_date = None
        earnings_date_confirmed_retrieved = False
        pays_dividends = False
        dividends_date_retrieved = None
else:
    st.write("Please enter a valid ticker symbol to proceed.")
    company_name = ""
    earnings_date = None
    earnings_date_confirmed_retrieved = False
    pays_dividends = False
    dividends_date_retrieved = None

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
            "Preis (Entry Price)", min_value=0.0, format="%.2f", key="entry_price"
        )

    with col2:
        order_type = st.radio(
            "Order Type", ["LMT", "MKT", "STP/STP LMT"], horizontal=True
        )


with st.container(border=True):

    col1, col2 = st.columns(2)
    with col1:
        initial_stop = st.number_input(
            "Initialer Stop (Initial Stop)", min_value=0.0, format="%.2f", key="initial_stop"
        )

    with col2:
        calculate_quantity = st.button(label="Calculate quantity")
        pass

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        # Removed session state for quantity and calculate dynamically
        if calculate_quantity:
            quantity = calculate_position_size(
                entry_price,
                initial_stop,
                account_balance,
                risk_per_trade_percent,
                risked_capital_percent,
            )
        else:
            quantity = 0  # Default value if not calculated

        # Replace the number input for quantity with a styled label and color it based on action
        quantity_color = "green" if initial_stop < entry_price else "red"
        quantity_label = f'<div style="color:{quantity_color}; font-weight:bold; font-size:30px; text-align:center;">{quantity}</div>'
        st.markdown(f"Menge (Quantity):<br>{quantity_label}", unsafe_allow_html=True)

        # Automatically toggle Aktion based on initial_stop and entry_price
        if initial_stop < entry_price:
            action = "Long"
        else:
            action = "Short"

    with col2:
        # Increase font size and center the label vertically
        if initial_stop < entry_price:
            action_label = '<div style="color:green; font-weight:bold; font-size:30px; text-align:center;">Long</div>'
        else:
            action_label = '<div style="color:red; font-weight:bold; font-size:30px; text-align:center;">Short</div>'
        st.markdown(f"Aktion:<br>{action_label}", unsafe_allow_html=True)

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
        "Warum eröffne ich die Position? (Reason for opening the position)", key="reason"
    )
    trade_management_plan = st.text_area(
        "Wie manage ich den Trade? (Trade Management Plan)", key="trade_management_plan"
    )

    plan_b = st.text_area("Was ist mein Plan B? (Plan B - Exit Scenario, Stop)", key="plan_b")

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
            "Action": {"select": {"name": action}},
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
