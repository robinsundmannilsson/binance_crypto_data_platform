import pytest
from datetime import datetime, timezone
from decimal import Decimal

from src.fetch_and_ingest import parse_candle

def test_parse_candle():
    raw = [123456789, "100.0", "200.0", "300.0", "400.0", "500.0", "600.0", "700.0", 8]
    symbol = "BTCUSDT"
    candle = parse_candle(raw, symbol)
    assert candle["symbol"] == symbol
    assert isinstance(candle["open_time"], datetime)
    assert isinstance(candle["open_price"], Decimal)
    assert isinstance(candle["high_price"], Decimal)
    assert isinstance(candle["low_price"], Decimal)
    assert isinstance(candle["close_price"], Decimal)
    assert isinstance(candle["volume"], Decimal)
    assert isinstance(candle["number_of_trades"], int)

def test_parse_candle_short_raw():
    raw = [123456789, "100.0", "200.0", "300.0", "400.0", "500.0"]
    symbol = "BTCUSDT"
    with pytest.raises(IndexError):
        parse_candle(raw, symbol)    

def test_open_time_utc():
    raw = [123456789, "100.0", "200.0", "300.0", "400.0", "500.0", "600.0", "700.0", 8]
    symbol = "BTCUSDT"
    candle = parse_candle(raw, symbol)
    assert candle["open_time"].tzinfo == timezone.utc