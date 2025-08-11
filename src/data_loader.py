import yfinance as yf
import pandas as pd
import streamlit as st
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data(ticker, period, interval, retries=3):
    try:
        logger.info(f"Загрузка данных: {ticker}, {period}, {interval}")
        
        # Используем Ticker вместо download для большей надежности
        t = yf.Ticker(ticker)
        
        # Определение периода для криптовалют
        if "-" in ticker and interval in ["1m", "5m", "15m", "30m"]:
            extended_period = "60d" if period in ["1d", "5d"] else period
            data = t.history(period=extended_period, interval=interval, auto_adjust=True)
        else:
            data = t.history(period=period, interval=interval, auto_adjust=True)

        # Повторные попытки при ошибках загрузки
        attempt = 0
        while (data is None or data.empty) and attempt < retries:
            attempt += 1
            logger.warning(f"Повторная попытка загрузки ({attempt}/{retries})")
            time.sleep(2)
            
            if "-" in ticker and interval in ["1m", "5m", "15m", "30m"]:
                data = t.history(period=extended_period, interval=interval, auto_adjust=True)
            else:
                data = t.history(period=period, interval=interval, auto_adjust=True)

        if data.empty:
            st.warning(f"Данные для {ticker} не найдены после {retries} попыток")
            logger.warning(f"Пустые данные для {ticker}")
            return pd.DataFrame()
            
        return data
    except Exception as e:
        st.error(f"Ошибка загрузки: {str(e)}")
        logger.error(f"Ошибка загрузки данных: {str(e)}")
        return pd.DataFrame()

# Функция для получения текущей цены
def get_current_price(symbol):
    try:
        # Для криптовалютных пар преобразуем формат
        if "/" in symbol:
            symbol = symbol.replace("/", "-")
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d', interval='1m')
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return 0
    except Exception as e:
        logger.error(f"Ошибка получения текущей цены: {str(e)}")
        return 0