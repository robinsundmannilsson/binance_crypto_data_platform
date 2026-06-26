import streamlit as st
import requests

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
st.header("This dashboard displays weekly candlestick data for selected cryptocurrencies")
st.subheader("Powered by Binance")

st.sidebar.header("Filtering Options")
st.sidebar.selectbox("Select Cryptocurrency Symbol", list(symbols.keys()), key="selected_symbol")