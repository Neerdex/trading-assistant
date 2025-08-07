import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime

def load_data(ticker, period, interval):
    try:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True
        )
        
        if data.empty or 'Close' not in data.columns:
            st.error(f"Данные для {ticker} не найдены. Попробуйте другой тикер.")
            return pd.DataFrame()
            
        try:
            ticker_obj = yf.Ticker(ticker)
            current_info = ticker_obj.fast_info
            current_price = current_info['lastPrice']
            last_close = data['Close'].iloc[-1].item()
            
            if current_price and last_close:
                discrepancy = abs(last_close - current_price)
                if discrepancy > last_close * 0.01:
                    st.warning(f"⚠️ Расхождение с текущей ценой: {discrepancy:.2f} ({discrepancy/last_close*100:.2f}%)")
                    st.write(f"Исторические данные: {last_close:.2f} | Текущая цена: {current_price:.2f}")
        except:
            pass
            
        return data
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {str(e)}")
        return pd.DataFrame()