
import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timezone
from decimal import Decimal

load_dotenv()

symbols = os.getenv("SYMBOLS").split(",")
interval = os.getenv("INTERVAL")
start_date = os.getenv("START_DATE")

BASE_URL = "https://api.binance.com/api/v3/klines"

start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
start_ms = int(start.timestamp() * 1000)

def parse_candle(raw: list, symbol: str) -> dict:
    return {
        "symbol": symbol,
        "open_time": datetime.fromtimestamp(raw[0] / 1000, tz=timezone.utc),
        "open_price": Decimal(raw[1]),
        "high_price": Decimal(raw[2]),
        "low_price": Decimal(raw[3]),
        "close_price": Decimal(raw[4]),
        "volume": Decimal(raw[5]),
        "number_of_trades": int(raw[8])
    }

params = {
    "interval": interval,
    "startTime": start_ms,
    "limit": 1000
}

for symbol in symbols:
    params["symbol"] = symbol
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    print(parse_candle(data[0], symbol))