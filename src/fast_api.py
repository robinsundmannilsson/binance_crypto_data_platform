from fastapi import FastAPI
from src.fetch_and_ingest import get_connection

app = FastAPI()

@app.get("/candles/{symbol}/latest")
def get_latest_candle(symbol: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""--sql
                        SELECT * FROM crypto_weekly_candles
                        WHERE symbol = %s
                        ORDER BY open_time DESC
                        LIMIT 1
                        """, (symbol,))
            return cur.fetchone()