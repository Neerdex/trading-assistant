from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
from config import Config
import logging
import time
import uuid

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaperTrader:
    def __init__(self):
        try:
            config = Config()
            config.validate()
            self.client = TradingClient(
                api_key=config.ALPACA_API_KEY,
                secret_key=config.ALPACA_SECRET_KEY,
                paper=True
            )
            self.symbol_lock = {}
            logger.info("PaperTrader успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации PaperTrader: {str(e)}")
            raise

    def get_account(self):
        try:
            return self.client.get_account()
        except Exception as e:
            logger.error(f"Ошибка получения аккаунта: {str(e)}")
            raise

    def place_order(self, symbol, qty, side):
        symbol = symbol.upper().replace("-", "/")
        op_id = str(uuid.uuid4())[:8]
        logger.info(f"[{op_id}] Начало операции: {symbol} {side} {qty}")
        
        try:
            # Проверка баланса перед размещением ордера
            if side.lower() == 'buy':
                account = self.get_account()
                if "/" in symbol:  # Для криптовалют
                    buying_power = float(account.buying_power)
                    from data_loader import get_current_price
                    current_price = get_current_price(symbol)
                    required = current_price * qty
                    
                    if required > buying_power:
                        raise Exception(f"Недостаточно средств. Требуется: ${required:.2f}, доступно: ${buying_power:.2f}")
            
            # Для ордеров Sell: проверка позиции
            if side.lower() == 'sell':
                positions = self.get_positions()
                position = next((p for p in positions if p.symbol == symbol), None)
                
                if not position:
                    raise Exception(f"Нет открытой позиции для {symbol} - невозможно продать")
                
                available_qty = float(position.qty)
                if qty > available_qty:
                    raise Exception(f"Попытка продать {qty}, доступно: {available_qty}")
            
            # Отменяем ВСЕ активные ордера для этого символа
            self.cancel_all_orders(symbol)
            time.sleep(1)  # Даем время на обработку отмены
            
            # Создаем ордер
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            
            # Размещаем ордер
            order = self.client.submit_order(order_data)
            logger.info(f"[{op_id}] Ордер размещен: {order.id}")
            
            return order
        except Exception as e:
            logger.error(f"[{op_id}] Ошибка размещения ордера: {str(e)}")
            raise

    def get_positions(self):
        try:
            return self.client.get_all_positions()
        except Exception as e:
            logger.error(f"Ошибка получения позиций: {str(e)}")
            return []

    def get_orders(self):
        """Получение всех ордеров"""
        try:
            return self.client.get_orders()
        except Exception as e:
            logger.error(f"Ошибка получения ордеров: {str(e)}")
            return []

    def cancel_all_orders(self, symbol=None):
        """Отмена всех активных ордеров"""
        try:
            orders = self.get_orders()
            if not orders:
                return True
                
            for order in orders:
                if order.status != OrderStatus.NEW:
                    continue
                if symbol and order.symbol != symbol:
                    continue
                    
                try:
                    self.client.cancel_order_by_id(order.id)
                    logger.info(f"Ордер #{order.id} отменен")
                    time.sleep(0.3)
                except Exception as e:
                    logger.error(f"Ошибка отмены ордера {order.id}: {str(e)}")
                    continue
                
            return True
        except Exception as e:
            logger.error(f"Ошибка отмены ордеров: {str(e)}")
            return False

    def close_position(self, symbol):
        symbol = symbol.upper().replace("-", "/")
        op_id = str(uuid.uuid4())[:8]
        logger.info(f"[{op_id}] Закрытие позиции: {symbol}")
        
        try:
            # Отменяем все активные ордера для этого символа
            self.cancel_all_orders(symbol)
            time.sleep(1)  # Даем время на обработку отмены
            
            # Получаем позицию
            position = next((p for p in self.get_positions() if p.symbol == symbol), None)
            if not position:
                logger.info(f"[{op_id}] Нет открытой позиции для {symbol}")
                return None
                
            # Закрываем позицию рыночным ордером
            qty = abs(float(position.qty))
            side = OrderSide.SELL if float(position.qty) > 0 else OrderSide.BUY
            
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.client.submit_order(order_data)
            logger.info(f"[{op_id}] Позиция закрыта: {order.id}")
            return order
        except Exception as e:
            logger.error(f"[{op_id}] Ошибка закрытия позиции: {str(e)}")
            raise

    def close_all_positions(self):
        op_id = str(uuid.uuid4())[:8]
        logger.info(f"[{op_id}] Закрытие всех позиций")
        
        try:
            # Отменяем все активные ордера
            self.cancel_all_orders()
            time.sleep(1)  # Даем время на обработку отмены
            
            # Получаем все позиции
            positions = self.get_positions()
            if not positions:
                logger.info(f"[{op_id}] Нет открытых позиций")
                return True
                
            # Закрываем каждую позицию с интервалом
            for pos in positions:
                try:
                    self.close_position(pos.symbol)
                    time.sleep(1)  # Задержка между закрытием позиций
                except Exception as e:
                    logger.error(f"[{op_id}] Ошибка закрытия позиции {pos.symbol}: {str(e)}")
                    continue
                    
            return True
        except Exception as e:
            logger.error(f"[{op_id}] Ошибка закрытия всех позиций: {str(e)}")
            raise