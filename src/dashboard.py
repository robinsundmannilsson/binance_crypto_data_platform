import streamlit as st
import requests
import base64
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

with open("assets/binance_logo.svg", "rb") as f:
    binance_logo = base64.b64encode(f.read()).decode()

st.set_page_config(
    page_title="Crypto Dashboard",
    layout="wide")

st.sidebar.markdown(f'Powered by <img src="data:image/svg+xml;base64,{binance_logo}" height="80" style="vertical-align: middle; margin-left: -12px; margin-top: -2px;">', unsafe_allow_html=True)
st.sidebar.header("Filtering Options")

symbols = {
    "Bitcoin (BTC)": "BTCUSDT",
    "Ethereum (ETH)": "ETHUSDT",
    "Ripple (XRP)": "XRPUSDT",
    "Solana (SOL)": "SOLUSDT",
    "Chainlink (LINK)": "LINKUSDT",
    "Cardano (ADA)": "ADAUSDT",
}

selected_symbol = st.sidebar.selectbox("Select Cryptocurrency Symbol", list(symbols.keys()), key="selected_symbol")
symbol = symbols[selected_symbol]

latest_price_response = requests.get(f"http://localhost:8000/candles/{symbol}/latest")
latest_price_data = latest_price_response.json()

historical_price_response = requests.get(f"http://localhost:8000/candles/{symbol}")
historical_price_data = historical_price_response.json()
df = pd.DataFrame(historical_price_data)

st.title("Daily Crypto Candlestick Data Dashboard")
st.subheader("This dashboard displays daily candlestick data for selected cryptocurrencies")

with st.container(border=True):
    st.subheader(f"Latest Daily Candlestick Data for {selected_symbol}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with st.container(border=True):
            st.metric("**Open Price**", float(latest_price_data["open_price"]))
    with col2:
        with st.container(border=True):
            st.metric("**High Price**", float(latest_price_data["high_price"]))
    with col3:
        with st.container(border=True):
            st.metric("**Low Price**", float(latest_price_data["low_price"]))
    with col4:
        with st.container(border=True):
            st.metric("**Close Price**", float(latest_price_data["close_price"]))

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.metric("**Volume**", float(latest_price_data["volume"]))
    with col2:
        with st.container(border=True):
            st.metric("**Number of Trades**", int(latest_price_data["number_of_trades"]))

fig = go.Figure(data=[go.Candlestick(x=df['open_time'],
                open=df['open_price'],
                high=df['high_price'],
                low=df['low_price'],
                close=df['close_price'])])

fig.update_layout(title=f'Daily Candlestick Chart for {selected_symbol}',
                  xaxis_title='Date',
                  yaxis_title='Price (USDT)',
                  xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

all_time_high = df["high_price"].astype(float).max()
st.metric("**All-Time High Price**", float(all_time_high))