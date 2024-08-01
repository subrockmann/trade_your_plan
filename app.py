from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
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
    if interval =="1d":
        data = yf.download(symbol, interval=interval)
        return data
    elif interval == "1h":
        # Calculate the start date (2 years ago from today)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=728)

        # Download the data
        data = yf.download(symbol, start=start_date.strftime('%Y-%m-%d'), interval='1h')
        data=yf.download(symbol, period="1y",interval=interval)
        return data

def point_pos(data, column):
    if data[column]==1:
        return data["RSI_14"]
    else:
        return None


def calculate_indicators(data, ema5_window, ema20_window, rsi_window):
    data["EMA_5"] = talib.EMA(data["Close"], timeperiod=ema5_window)
    data["EMA_20"] = talib.EMA(data["Close"], timeperiod=ema20_window)
    data["RSI_14"] = talib.RSI(data["Close"], timeperiod=rsi_window)
    data["SMA_RSI_14"] = data["RSI_14"].rolling(window=14).mean()
    # data["signal_1"] = ((data["RSI_14"].shift(1) < data["SMA_RSI_14"].shift(1)) & (data["RSI_14"] >= data["SMA_RSI_14"])).astype(int)
    data["point_pos_signal_2"] = ((data["Adj Close"].shift(1) < data["EMA_20"].shift(1)) & (data["Adj Close"] >= data["EMA_20"])).astype(int)
    data["signal_3"] = ((data["EMA_5"].shift(1) < data["EMA_20"].shift(1)) & (data["EMA_5"] >= data["EMA_20"])).astype(int)
    data["signal_1"] = ((data["RSI_14"] >= data["SMA_RSI_14"])).astype(int)
    data["point_pos_signal_1"] = (
        (data["RSI_14"].shift(1) < data["SMA_RSI_14"].shift(1))
        & (data["RSI_14"] >= data["SMA_RSI_14"])
    ).astype(int)

    # data["point_pos_signal_1"] = data.apply(lambda x: point_pos(x, "signal_1"), axis=1)
    data["signal_2"] = ((data["Adj Close"] >= data["EMA_20"])).astype(int)
    # data["stop_price"] =
    # data["signal_3"] = ((data["EMA_5"] >= data["EMA_20"])).astype(int)
    data["long_signal"] = ((data["signal_1"] + data["signal_2"] + data["signal_3"]) == 3).astype(int)
    # data.reset_index(drop=False, inplace=True)
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
    fig.add_trace(go.Candlestick(x=data.index, # data["Datetime"],#.index,
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

    # Filter out NaN values for point_pos_signal_1
    signal_1_data = data[data["point_pos_signal_1"]==1]

    fig.add_trace(
        go.Scatter(
            x=signal_1_data.index,
            y=signal_1_data["point_pos_signal_1"],
            mode="markers",
            marker=dict(size=5, color="black"),
        ),
        row=2,
        col=1,
    )

    # # Add background shading based on signal_1
    # for i in range(len(data) - 1):
    #     if data["signal_1"].iloc[i] == 1:
    #         fig.add_shape(
    #             type="rect",
    #             x0=data.index[i],
    #             x1=data.index[i + 1],
    #             y0=0,
    #             y1=1,
    #             xref="x",
    #             yref="paper",
    #             fillcolor="LightGreen",
    #             opacity=0.5,
    #             layer="below",
    #             line_width=0,
    #         )

    # Add shapes to highlight candles with signal_2

    shapes = []
    for idx in data.index[data["point_pos_signal_2"] == 1]:
        shapes.append(
            {
                "type": "rect",
                "x0": idx,
                "x1": idx,
                "y0": data.loc[idx, "Low"],
                "y1": data.loc[idx, "High"],
                "xref": "x",
                "yref": "y",
                "fillcolor": "pink",
                "opacity": 0.2,
                "line_width": 1,
                "layer": "above",
            }
        )

    # Add background shading based on signal_1

    in_signal = False
    for i in range(len(data)):
        if data["signal_1"].iloc[i] == 1 and not in_signal:
            start_idx = data.index[i]
            in_signal = True
        elif data["signal_1"].iloc[i] == 0 and in_signal:
            end_idx = data.index[i]
            shapes.append(
                {
                    "type": "rect",
                    "x0": start_idx,
                    "x1": end_idx,
                    "y0": 0,
                    "y1": 1,
                    "xref": "x",
                    "yref": "paper",
                    "fillcolor": "LightGreen",
                    "opacity": 0.5,
                    "layer": "below",
                    "line_width": 0,
                }
            )
            in_signal = False

    # Handle case where the signal extends to the end of the data
    if in_signal:
        end_idx = data.index[-1]
        shapes.append(
            {
                "type": "rect",
                "x0": start_idx,
                "x1": end_idx,
                "y0": 0,
                "y1": 1,
                "xref": "x",
                "yref": "paper",
                "fillcolor": "LightGreen",
                "opacity": 0.5,
                "layer": "below",
                "line_width": 0,
            }
        )

    # Update layout with shapes
    fig.update_layout(shapes=shapes)

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

    candles = st.sidebar.number_input("Number of candles", min_value=30, max_value=1000, value=300)

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

    # Remove weekends from the data
    data = data[data.index.weekday < 5]
    data.reset_index(inplace=True)
    data.rename(columns={'index': 'Datetime'}, inplace=True)

    # Calculate indicators
    data = calculate_indicators(data, ema5_window, ema20_window, rsi_window)

    data_reduced = data[-candles:-1]
    signal_indices = data_reduced[data_reduced["long_signal"] == 1].index
    # signal_indices = data[

    #     (data["signal_1"] == 1) & (data["signal_2"] == 1) & (data["signal_3"] == 1)
    # ].index

    # Plot data
    fig = plot_data(data_reduced, indices=signal_indices)
    # fig = plot_data(data)
    st.plotly_chart(fig, use_container_width=True)  # Use full width of the container


if __name__ == "__main__":
    main()
