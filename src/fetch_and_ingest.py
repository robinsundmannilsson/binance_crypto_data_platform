import requests
from datetime import datetime, timezone
from decimal import Decimal

BASE_URL = "https://api.binance.com/api/v3/klines"

start = datetime(2020, 1, 1, tzinfo=timezone.utc)
start_ms = int(start.timestamp() * 1000)

params = {
    "symbol": "BTCUSDT",
    "interval": "1w",
    "startTime": start_ms,
    "limit": 1000
}

response = requests.get(BASE_URL, params=params)
response.raise_for_status()

data = response.json()

def parse_candle(raw: list) -> dict:
    return {
        "open_time": datetime.fromtimestamp(raw[0] / 1000, tz=timezone.utc),
        "open_price": Decimal(raw[1]),
        "high_price": Decimal(raw[2]),
        "low_price": Decimal(raw[3]),
        "close_price": Decimal(raw[4]),
        "volume": Decimal(raw[5]),
        "number_of_trades": int(raw[8])
    }

print(parse_candle(data[0]))