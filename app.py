from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import talib
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(layout="wide")

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
    #data["signal_1"] = ((data["RSI_14"].shift(1) < data["SMA_RSI_14"].shift(1)) & (data["RSI_14"] >= data["SMA_RSI_14"])).astype(int)
    #data["signal_2"] = ((data["Adj Close"].shift(1) < data["EMA_20"].shift(1)) & (data["Adj Close"] >= data["EMA_20"])).astype(int)
    data["signal_3"] = ((data["EMA_5"].shift(1) < data["EMA_20"].shift(1)) & (data["EMA_5"] >= data["EMA_20"])).astype(int)
    data["signal_1"] = ((data["RSI_14"] >= data["SMA_RSI_14"])).astype(int)
    data["signal_2"] = ((data["Adj Close"] >= data["EMA_20"])).astype(int)
    #data["signal_3"] = ((data["EMA_5"] >= data["EMA_20"])).astype(int)
    data["long_signal"] = ((data["signal_1"] + data["signal_2"] + data["signal_3"]) == 3).astype(int)
    #data.reset_index(drop=False, inplace=True)
    return data


# Function to plot data
def plot_data(data, indices=[]):
    global company_name
    config = {"scrollZoom": True}
    # Create a figure with two rows and shared x-axis
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.2,
        row_heights=[0.8, 0.2],
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
    # Get the last 30 candles
    last_30_candles = data.iloc[-30:]

    # Calculate the initial x-axis range (e.g., last 30 candles)
    initial_x_range = [last_30_candles.index.min(), last_30_candles.index.max()]

    fig.update_layout(
        height=800,  # Set the height of the plot
        title=f"{company_name} Stock Price with Indicators and RSI",
        xaxis_title="Date",
        #xaxis_range=initial_x_range,  # Set initial x-axis range
        #xaxis_range=[start_date, end_date],
        # xaxis_range=[pd.datetime(2013, 10, 17),
        #                        pd.datetime(2013, 11, 20)],
        yaxis_title="Price",
        yaxis2=dict(title="RSI", range=[0, 100]),
        legend=dict(x=0, y=1, traceorder="normal"),
        # template="plotly_dark",
        # yaxis=dict(scaleanchor="x", scaleratio=1),
        # yaxis=dict(constrain="domain", domain=[0, 1]),
        # yaxis_range=[
        #     data["Close"].min(),
        #     data["Close"].max(),
        # ],  # Set initial y-axis range
        # uirevision="yaxis.range",  # Enable the vertical zoom bar
        yaxis_fixedrange=False,
        xaxis_range=[datetime(2013, 10, 17),
                               datetime(2013, 11, 20)]
    )

    # Add vertical lines at specified indices
    for index in indices:
        fig.add_shape(
            type="line",
            x0=index,
            x1=index,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(color="red", width=2),
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
    global end_date, start_date
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
    signal_indices = data[data["long_signal"] == 1].index
    # signal_indices = data[
    #     (data["signal_1"] == 1) & (data["signal_2"] == 1) & (data["signal_3"] == 1)
    # ].index

    # Plot data
    fig = plot_data(data, indices=signal_indices)
    #fig = plot_data(data)
    st.plotly_chart(fig, use_container_width=True)  # Use full width of the container


if __name__ == "__main__":
    main()
