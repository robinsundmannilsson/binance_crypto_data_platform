import streamlit as st
import requests
import base64

with open("assets/binance_logo.svg", "rb") as f:
    binance_logo = base64.b64encode(f.read()).decode()

symbols = {
    "Bitcoin (BTC)": "BTCUSDT",
    "Ethereum (ETH)": "ETHUSDT",
    "Ripple (XRP)": "XRPUSDT",
    "Solana (SOL)": "SOLUSDT",
    "Chainlink (LINK)": "LINKUSDT",
    "Cardano (ADA)": "ADAUSDT",
}

st.set_page_config(
    page_title="Crypto Dashboard",
    layout="wide")

st.title("Weekly Crypto Candlestick Data Dashboard")
st.subheader("This dashboard displays weekly candlestick data for selected cryptocurrencies")

st.sidebar.markdown(f'Powered by <img src="data:image/svg+xml;base64,{binance_logo}" height="80" style="vertical-align: middle; margin-left: -12px; margin-top: -2px;">', unsafe_allow_html=True)
st.sidebar.header("Filtering Options")
st.sidebar.selectbox("Select Cryptocurrency Symbol", list(symbols.keys()), key="selected_symbol")

