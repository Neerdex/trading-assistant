import matplotlib
matplotlib.use('Agg')  # Важно: исправляет проблемы с бэкендом

import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf

st.title("🚀 Мой Trading Assistant")
ticker = st.text_input("Введите тикер (например AAPL):", "AAPL")

if ticker:
    try:
        # Загрузка данных с явным указанием auto_adjust
        data = yf.download(ticker, period="3mo", auto_adjust=True)
        
        # Проверка наличия данных
        if data.empty:
            st.error("Не удалось загрузить данные. Проверьте тикер.")
        else:
            st.success(f"Данные для {ticker} загружены успешно!")
            st.write(f"Последняя цена: ${data['Close'][-1]:.2f}")
            
            # Создаем отдельную фигуру для mplfinance
            fig, axlist = mpf.plot(
                data,
                type='candle',
                style='charles',
                title=f"{ticker} Price",
                ylabel="Price ($)",
                returnfig=True,
                show_nontrading=False
            )
            
            # Отображаем график в Streamlit
            st.pyplot(fig)
            
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        # Для отладки выведем полную ошибку в консоль
        import traceback
        traceback.print_exc()