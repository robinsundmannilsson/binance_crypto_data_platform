import streamlit as st
import requests
import base64

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

st.title("Weekly Crypto Candlestick Data Dashboard")
st.subheader("This dashboard displays weekly candlestick data for selected cryptocurrencies")

with st.container(border=True):
    st.subheader(f"Latest Weekly Candlestick Data for {selected_symbol}")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
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
    with col5:
        with st.container(border=True):
            st.metric("**Volume**", float(latest_price_data["volume"]))
    with col6:
        with st.container(border=True):
            st.metric("**Number of Trades**", int(latest_price_data["number_of_trades"]))
