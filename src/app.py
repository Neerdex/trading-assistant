import matplotlib
matplotlib.use('Agg')
import streamlit as st
import yfinance as yf
import mplfinance as mpf
import pandas as pd
from datetime import datetime, timedelta

# Кэшируем загрузку данных для ускорения работы
@st.cache_data(ttl=3600)  # Обновляем каждый час
def load_data(ticker, period, interval):
    return yf.download(ticker, period=period, interval=interval, auto_adjust=True)

# Функция расчета RSI
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Настройка страницы
st.set_page_config(page_title="Trading Assistant", layout="wide")
st.title("🚀 Мой Trading Assistant")

# Сайдбар для настроек
with st.sidebar:
    st.header("Настройки данных")
    ticker = st.text_input("Тикер (например AAPL):", "AAPL")
    
    # Выбор периода
    period_options = ["1д", "1нед", "1мес", "3мес", "6мес", "1год", "макс"]
    period = st.selectbox("Период:", period_options, index=2)
    period_map = {"1д": "1d", "1нед": "1wk", "1мес": "1mo", 
                 "3мес": "3mo", "6мес": "6mo", "1год": "1y", "макс": "max"}
    
    # Выбор интервала
    interval_options = ["1м", "5м", "15м", "30м", "1ч", "1д", "1нед"]
    interval = st.selectbox("Интервал:", interval_options, index=5)
    interval_map = {"1м": "1m", "5м": "5m", "15м": "15m", 
                  "30м": "30m", "1ч": "1h", "1д": "1d", "1нед": "1wk"}
    
    # Тех. индикаторы
    st.header("Технические индикаторы")
    show_sma = st.checkbox("SMA (20 периодов)", True)
    show_rsi = st.checkbox("RSI (14 периодов)", True)

if ticker:
    try:
        # Загрузка данных
        data = load_data(ticker, period_map[period], interval_map[interval])
        
        if data.empty:
            st.error("Не удалось загрузить данные. Проверьте тикер.")
        else:
            # Расчет индикаторов
            if show_sma:
                data['SMA_20'] = data['Close'].rolling(window=20).mean()
                
            if show_rsi:
                data['RSI_14'] = calculate_rsi(data)
            
            # Отображение основной информации
            last_close = data['Close'][-1]
            prev_close = data['Close'][-2] if len(data) > 1 else last_close
            change = ((last_close - prev_close) / prev_close) * 100
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Текущая цена", f"${last_close:.2f}")
            col2.metric("Изменение", f"{change:.2f}%", 
                       delta_color="inverse" if change < 0 else "normal")
            col3.metric("Последнее обновление", data.index[-1].strftime('%Y-%m-%d %H:%M'))
            
            # Настройка индикаторов для графика
            add_plots = []
            if show_sma:
                add_plots.append(mpf.make_addplot(data['SMA_20'], color='blue'))
            
            # Создание графиков
            fig, axes = mpf.plot(
                data,
                type='candle',
                style='charles',
                title=f"{ticker} | {period} | {interval}",
                ylabel="Цена ($)",
                addplot=add_plots,
                returnfig=True,
                figsize=(12, 6),
                volume=True if 'Volume' in data.columns else False,
                show_nontrading=False,
                panel_ratios=(4, 1)
            )
            
            # Отображение RSI в отдельной панели
            if show_rsi:
                ax_rsi = axes[0].twinx()
                ax_rsi.plot(data.index, data['RSI_14'], color='purple', alpha=0.7)
                ax_rsi.axhline(30, color='green', linestyle='--', alpha=0.5)
                ax_rsi.axhline(70, color='red', linestyle='--', alpha=0.5)
                ax_rsi.set_ylabel('RSI', color='purple')
                ax_rsi.tick_params(axis='y', labelcolor='purple')
                ax_rsi.set_ylim(0, 100)
            
            st.pyplot(fig)
            
            # Анализ RSI
            if show_rsi:
                st.subheader("Анализ RSI")
                last_rsi = data['RSI_14'].iloc[-1]
                st.write(f"Текущее значение RSI: **{last_rsi:.2f}**")
                
                if last_rsi < 30:
                    st.success("Сигнал: ПЕРЕПРОДАННОСТЬ (RSI < 30)")
                    st.info("Традиционная интерпретация: Возможен разворот вверх")
                elif last_rsi > 70:
                    st.warning("Сигнал: ПЕРЕКУПЛЕННОСТЬ (RSI > 70)")
                    st.info("Традиционная интерпретация: Возможен разворот вниз")
                else:
                    st.info("RSI в нейтральной зоне (30-70)")
                
                # Визуализация RSI
                st.write("**История RSI за выбранный период:**")
                st.line_chart(data['RSI_14'])
            
            # Дополнительная информация
            st.subheader("Последние 5 записей")
            st.dataframe(data.tail(5))
            
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        st.stop()