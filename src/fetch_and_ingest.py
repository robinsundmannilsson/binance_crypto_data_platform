
import os
import requests
from datetime import datetime, timezone
from decimal import Decimal
from dotenv import load_dotenv
import psycopg2
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)

def get_connection():
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT")
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        host=db_host,
        password=db_password,
        port=db_port
    )
    return conn

def create_table_if_not_exists(cur):
    cur.execute("""--sql
    CREATE TABLE IF NOT EXISTS crypto_daily_candles (
        symbol TEXT NOT NULL,
        open_time TIMESTAMP WITH TIME ZONE NOT NULL,
        open_price NUMERIC (20,8) NOT NULL,
        high_price NUMERIC (20,8) NOT NULL,
        low_price NUMERIC (20,8) NOT NULL,
        close_price NUMERIC (20,8) NOT NULL,
        volume NUMERIC (20,8) NOT NULL,
        number_of_trades INTEGER NOT NULL,
        PRIMARY KEY (symbol, open_time)
    )
    """)

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

def insert_candle(cur, candle):
    candle_data = (
        candle["symbol"],
        candle["open_time"],
        candle["open_price"],
        candle["high_price"],
        candle["low_price"],
        candle["close_price"],
        candle["volume"],
        candle["number_of_trades"]
        )
    cur.execute("""--sql
    INSERT INTO crypto_daily_candles
    (symbol, open_time, open_price, high_price, low_price, close_price, volume, number_of_trades)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (symbol, open_time) DO UPDATE
    SET open_price = EXCLUDED.open_price,
        high_price = EXCLUDED.high_price,
        low_price = EXCLUDED.low_price,
        close_price = EXCLUDED.close_price,
        volume = EXCLUDED.volume,
        number_of_trades = EXCLUDED.number_of_trades
    """, candle_data)

if __name__ == "__main__":

    base_url = os.getenv("BASE_URL")
    symbols = os.getenv("SYMBOLS").split(",")
    interval = os.getenv("INTERVAL")
    start_date = os.getenv("START_DATE")

    start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_ms = int(start.timestamp() * 1000)

    params = {
        "interval": interval,
        "startTime": start_ms,
        "limit": 1000
    }

    with get_connection() as conn:
        with conn.cursor() as cur:

            logging.info("Creating table if it does not exist...")
            create_table_if_not_exists(cur)

            for symbol in symbols:
                params["symbol"] = symbol
                params["startTime"] = start_ms
                try:
                    logging.info(f"Fetching data for {symbol}...")
                    response = requests.get(base_url, params=params)
                    response.raise_for_status()

                    total = 0

                    while True:
                        page = response.json()
                        for raw_candle in page:
                            candle = parse_candle(raw_candle, symbol)
                            insert_candle(cur, candle)
                        total += len(page)
                        if len(page) < 1000:
                            break
                        params["startTime"] = page[-1][0] + 1
                        logging.info(f"Fetching next page for {symbol}...")
                        response = requests.get(base_url, params=params)
                        response.raise_for_status()

                    logging.info(f"Done with {symbol}, {total} candles inserted.")
                except requests.RequestException as e:
                    logging.error(f"Error fetching data for {symbol}: {e}")
                    continue