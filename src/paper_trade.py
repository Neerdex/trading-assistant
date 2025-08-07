from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
# ИЗМЕНЁННЫЙ ИМПОРТ:
from config import Config

class PaperTrader:
    def __init__(self):
        config = Config()
        config.validate()
        self.client = TradingClient(
            api_key=config.ALPACA_API_KEY,
            secret_key=config.ALPACA_SECRET_KEY,
            paper=True
        )
    
    def get_account(self):
        return self.client.get_account()
    
    def place_order(self, symbol, qty, side):
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
            time_in_force=TimeInForce.GTC
        )
        return self.client.submit_order(order_data)
    
    def get_positions(self):
        return self.client.get_all_positions()
    
    def get_orders(self, status='open'):
        return self.client.get_orders(status=status)
    
    def close_position(self, symbol):
        return self.client.close_position(symbol)
    
    def close_all_positions(self):
        positions = self.get_positions()
        for pos in positions:
            self.close_position(pos.symbol)
        return True