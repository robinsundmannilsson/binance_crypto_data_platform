from fastapi import FastAPI
from src.fetch_and_ingest import get_connection
from src.models import CandleResponse
from psycopg2.extras import RealDictCursor
from datetime import date

app = FastAPI()

@app.get("/candles/{symbol}", response_model=list[CandleResponse])
def get_candle(symbol: str, from_date: date = None, to_date: date = None):
    query = """--sql
            SELECT
            symbol,
            open_time AT TIME ZONE 'UTC' AS open_time,
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
            number_of_trades
            FROM crypto_weekly_candles
            WHERE symbol = %s
            """
    params = [symbol]
    if from_date:
        query += " AND open_time >= %s"
        params.append(from_date)
    if to_date:
        query += " AND open_time <= %s"
        params.append(to_date)
    query += " ORDER BY open_time DESC"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()

@app.get("/candles/{symbol}/latest", response_model=CandleResponse)
def get_latest_candle(symbol: str):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""--sql
                        SELECT
                            symbol,
                            open_time AT TIME ZONE 'UTC' AS open_time,
                            open_price,
                            high_price,
                            low_price,
                            close_price,
                            volume,
                            number_of_trades
                        FROM crypto_weekly_candles
                        WHERE symbol = %s
                        ORDER BY open_time DESC
                        LIMIT 1
                        """, (symbol,))
            return cur.fetchone()