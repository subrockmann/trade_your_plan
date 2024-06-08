from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import talib
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import streamlit as st


# Define the available intervals
intervals = [
    "1m",
    "2m",
    "5m",
    "15m",
    "30m",
    "60m",
    "90m",
    "1h",
    "1d",
    "5d",
    "1wk",
    "1mo",
    "3mo",
]


def download_data(symbol, interval):
    data = yf.download(symbol, interval=interval)
    return data


def calculate_indicators(data, ema5_window, ema20_window, rsi_window):
    data["EMA_5"] = talib.EMA(data["Close"], timeperiod=ema5_window)
    data["EMA_20"] = talib.EMA(data["Close"], timeperiod=ema20_window)
    data["RSI_14"] = talib.RSI(data["Close"], timeperiod=rsi_window)
    data["SMA_RSI_14"] = data["RSI_14"].rolling(window=14).mean()
    return data


# def plot_data(data):
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode="lines", name="Close"))
#     fig.add_trace(
#         go.Scatter(x=data.index, y=data["MA"], mode="lines", name="Moving Average")
#     )
#     fig.add_trace(go.Scatter(x=data.index, y=data["EMA_5"], mode="lines", name="EMA 5"))
#     fig.add_trace(
#         go.Scatter(x=data.index, y=data["EMA_20"], mode="lines", name="EMA 20")
#     )
#     fig.add_trace(
#         go.Scatter(
#             x=data.index, y=data["RSI_14"], mode="lines", name="RSI 14", yaxis="y2"
#         )
#     )

#     # Add a secondary y-axis for RSI
#     fig.update_layout(
#         title="Stock Price with Indicators",
#         xaxis_title="Date",
#         yaxis_title="Price",
#         yaxis2=dict(title="RSI", overlaying="y", side="right", range=[0, 100]),
#         legend=dict(x=0, y=1, traceorder="normal"),
#         template="plotly_dark",
#     )

#     return fig


# Function to plot data
def plot_data(data):
    global company_name
    # Create a figure with two rows and shared x-axis
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3],
        subplot_titles=("Stock Price with Indicators", "RSI"),
    )

    # Add traces for the main plot (Price and Moving Averages)
    # fig.add_trace(
    #     go.Scatter(x=data.index, y=data["Close"], mode="lines", name="Close"),
    #     row=1,
    #     col=1,
    # )
    fig.add_trace(go.Candlestick(x=data.index,
                                 open=data['Open'],
                                 high=data['High'],
                                 low=data['Low'],
                                 close=data['Close'],
                                 name='Candlesticks'), 
                                 row=1, col=1)

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["EMA_5"],
            mode="lines",
            name="EMA 5",
            line=dict(color="blue"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["EMA_20"],
            mode="lines",
            name="EMA 20",
            line=dict(color="black"),
        ),
        row=1,
        col=1,
    )

    # Add trace for the RSI plot
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["RSI_14"],
            mode="lines",
            name="RSI 14",
            line=dict(color="grey"),
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["SMA_RSI_14"],
            mode="lines",
            name="SMA of RSI 14",
            line=dict(color="green"),
        ),
        row=2,
        col=1,
    )

    # Update layout for the figure
    fig.update_layout(
        height=800,  # Set the height of the plot
        title=f"{company_name} Stock Price with Indicators and RSI",
        xaxis_title="Date",
        yaxis_title="Price",
        yaxis2=dict(title="RSI", range=[0, 100]),
        legend=dict(x=0, y=1, traceorder="normal"),
        # template="plotly_dark",
        # yaxis=dict(scaleanchor="x", scaleratio=1),
        #yaxis=dict(constrain="domain", domain=[0, 1]),
        # yaxis_range=[
        #     data["Close"].min(),
        #     data["Close"].max(),
        # ],  # Set initial y-axis range
        #uirevision="yaxis.range",  # Enable the vertical zoom bar
        yaxis_fixedrange= False
    )

    return fig


def main():
    symbol = st.text_input("Ticker Symbol", "AAPL")
    ticker = yf.Ticker(symbol)
    global company_name
    company_name = ticker.info["shortName"]

    st.markdown(f"{company_name}")
    st.sidebar.title("Financial Analysis Tool")

    # User inputs in sidebar
    interval = st.sidebar.selectbox(
        "Select Interval", intervals, index=intervals.index("1d")
    )
    end_date = st.sidebar.date_input("End Date", datetime.today().date())
    start_date = st.sidebar.date_input("Start Date", end_date - timedelta(days=30))

    # end_date = datetime.today().date()
    # start_date = end_date - timedelta(days=30)

    ema5_window = st.sidebar.number_input(
        "EMA 5 Window", min_value=1, max_value=365, value=5
    )
    ema20_window = st.sidebar.number_input(
        "EMA 20 Window", min_value=1, max_value=365, value=20
    )
    rsi_window = st.sidebar.number_input(
        "RSI 14 Window", min_value=1, max_value=365, value=14
    )

    # Download data
    data = download_data(symbol, interval)

    # Calculate indicators
    data = calculate_indicators(data, ema5_window, ema20_window, rsi_window)

    # Plot data
    fig = plot_data(data)
    st.plotly_chart(fig, use_container_width=True)  # Use full width of the container


if __name__ == "__main__":
    main()
