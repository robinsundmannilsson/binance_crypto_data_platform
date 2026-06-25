from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

class CandleResponse(BaseModel):
    symbol: str = Field(description="The symbol of the cryptocurrency")
    open_time: datetime = Field(description="The opening timestamp of the candle")
    open_price: Decimal = Field(description="The opening price of the candle")
    high_price: Decimal = Field(description="The highest price of the candle")
    low_price: Decimal = Field(description="The lowest price of the candle")
    close_price: Decimal = Field(description="The closing price of the candle")
    volume: Decimal = Field(description="The trading volume of the candle")
    number_of_trades: int = Field(description="The number of trades during the candle period")