import pandas as pd
import numpy as np
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_technical_indicators(data):
    try:
        # Простой расчет SMA
        if len(data) >= 20: 
            data['SMA20'] = data['Close'].rolling(window=20).mean()
        if len(data) >= 50: 
            data['SMA50'] = data['Close'].rolling(window=50).mean()

        # Расчет RSI
        if len(data) >= 14:
            delta = data['Close'].diff(1)
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            # Избегаем деления на ноль
            avg_loss = avg_loss.replace(0, 0.001)
            
            rs = avg_gain / avg_loss
            data['RSI'] = 100 - (100 / (1 + rs))

        return data
    except Exception as e:
        logger.error(f"Ошибка расчета индикаторов: {str(e)}")
        return data