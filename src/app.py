import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# Настройки
st.set_page_config(
    page_title="Трейдинг Помощник",
    layout="wide",
    page_icon="💹"
)
st.title("💹 Трейдинг Помощник")

# Инициализация состояния сессии
if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False

# Функция загрузки данных с улучшенной обработкой ошибок
def load_data(ticker, period, interval):
    try:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True
        )
        
        # Проверяем, что данные загружены и есть столбец 'Close'
        if data.empty or 'Close' not in data.columns:
            st.error(f"Данные для {ticker} не найдены. Попробуйте другой тикер.")
            return pd.DataFrame()
            
        # Проверка расхождений с текущей ценой
        try:
            ticker_obj = yf.Ticker(ticker)
            current_info = ticker_obj.fast_info
            current_price = current_info['lastPrice']
            last_close = data['Close'].iloc[-1].item()
            
            if current_price and last_close:
                discrepancy = abs(last_close - current_price)
                if discrepancy > last_close * 0.01:  # >1% расхождения
                    st.warning(f"⚠️ Расхождение с текущей ценой: {discrepancy:.2f} ({discrepancy/last_close*100:.2f}%)")
                    st.write(f"Исторические данные: {last_close:.2f} | Текущая цена: {current_price:.2f}")
        except:
            pass
            
        return data
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {str(e)}")
        return pd.DataFrame()

# Сайдбар
with st.sidebar:
    st.header("Настройки")
    ticker = st.text_input("Тикер (AAPL, BTC-USD):", "AAPL")
    
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox(
            "Период",
            ["1d", "5d", "1mo", "3mo", "6mo", "1y", "max"],
            index=2
        )
    with col2:
        interval = st.selectbox(
            "Интервал",
            ["1m", "5m", "15m", "30m", "1h", "1d"],
            index=5
        )
    
    if st.button("Обновить данные", type="primary"):
        st.session_state.run_analysis = True

# Основной интерфейс
if st.session_state.run_analysis:
    try:
        with st.spinner("Загрузка данных..."):
            data = load_data(ticker, period, interval)
            
        if data.empty:
            st.warning("Нет данных для отображения. Проверьте параметры и попробуйте снова.")
        else:
            # Основные метрики с проверкой на достаточность данных
            if len(data) > 1:
                last_close = data['Close'].iloc[-1].item()
                prev_close = data['Close'].iloc[-2].item()
                change_pct = round(((last_close - prev_close) / prev_close * 100), 2)
            else:
                last_close = data['Close'].iloc[0].item() if len(data) == 1 else 0
                change_pct = 0
                st.warning("Мало данных для расчета изменения цены")
            
            st.success(f"Данные загружены | {ticker} | {period} | {interval}")
            
            # Показываем метрики только если есть данные
            if last_close > 0:
                metric_col1, metric_col2 = st.columns(2)
                metric_col1.metric("Текущая цена", f"{last_close:.2f}")
                metric_col2.metric("Изменение", f"{change_pct}%", 
                                  delta_color="inverse" if change_pct < 0 else "normal")
            
            # Графики
            if not data.empty and len(data) > 1:
                # Простой линейный график как fallback
                st.subheader("Линейный график")
                st.line_chart(data['Close'])
                
                # Свечной график с улучшениями
                try:
                    fig = go.Figure(data=[go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name="Цены",
                        increasing_line_color='green',
                        decreasing_line_color='red'
                    )])
                    
                    # Добавляем скользящие средние
                    if len(data) > 20:
                        data['SMA20'] = data['Close'].rolling(window=20).mean()
                        fig.add_trace(go.Scatter(
                            x=data.index,
                            y=data['SMA20'],
                            name='SMA 20',
                            line=dict(color='blue', width=2)
                        ))
                    
                    if len(data) > 50:
                        data['SMA50'] = data['Close'].rolling(window=50).mean()
                        fig.add_trace(go.Scatter(
                            x=data.index,
                            y=data['SMA50'],
                            name='SMA 50',
                            line=dict(color='orange', width=2)
                        ))
                    
                    fig.update_layout(
                        title=f"{ticker} - Свечной график",
                        xaxis_title="Дата",
                        yaxis_title="Цена ($)",
                        height=600,
                        template="plotly_white",
                        showlegend=True,
                        xaxis_rangeslider_visible=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Ошибка построения свечного графика: {str(e)}")
                    st.write("Используем линейный график как запасной вариант")
            
            # Исторические данные
            with st.expander("📋 Подробные исторические данные"):
                st.dataframe(data.tail(20).sort_index(ascending=False))
                
            # Информация о качестве данных
            with st.expander("🔍 Информация о данных"):
                st.write(f"**Период данных:** {data.index[0].strftime('%Y-%m-%d')} - {data.index[-1].strftime('%Y-%m-%d')}")
                st.write(f"**Количество точек:** {len(data)}")
                st.write(f"**Источник:** Yahoo Finance")
                st.write(f"**Последнее обновление:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
    except Exception as e:
        st.error(f"Критическая ошибка: {str(e)}")
        st.write("Параметры запроса:")
        st.write(f"- Тикер: {ticker}")
        st.write(f"- Период: {period}")
        st.write(f"- Интервал: {interval}")
        # Выводим дополнительную информацию для отладки
        st.write("Информация о данных:")
        st.write(f"Количество строк: {len(data)}")
        st.write(f"Колонки: {data.columns.tolist()}")
        if not data.empty:
            st.write("Последние 5 строк:")
            st.write(data.tail())
else:
    st.info("Задайте параметры и нажмите 'Обновить данные'")
    st.image("https://via.placeholder.com/800x400?text=График+появится+после+загрузки", 
             caption="Пример интерфейса")