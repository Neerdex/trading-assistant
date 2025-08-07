import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
# ИЗМЕНЁННЫЕ ИМПОРТЫ:
from data_loader import load_data
from indicators import add_technical_indicators
from paper_trade import PaperTrader

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

# Инициализация PaperTrader
try:
    trader = PaperTrader()
    alpaca_available = True
except Exception as e:
    st.error(f"Ошибка инициализации PaperTrader: {str(e)}")
    trader = None
    alpaca_available = False

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
        
    # Раздел Paper Trading
    if alpaca_available:
        st.divider()
        st.header("📊 Paper Trading")
        
        try:
            account = trader.get_account()
            st.success("✅ Подключение к Alpaca успешно")
            st.caption(f"Баланс: ${account.equity} | Валюта: {account.currency}")
        except Exception as e:
            st.error(f"Ошибка подключения к Alpaca: {str(e)}")
        
        # Форма для ордеров
        with st.form("order_form"):
            st.subheader("Разместить ордер")
            order_symbol = st.text_input("Тикер ордера", ticker)
            order_qty = st.number_input("Количество", min_value=1, max_value=100, value=1)
            order_side = st.radio("Тип операции", ["Buy", "Sell"], index=0)
            
            if st.form_submit_button("Отправить ордер"):
                try:
                    order = trader.place_order(order_symbol, order_qty, order_side)
                    st.success(f"Ордер #{order.id} успешно размещен!")
                except Exception as e:
                    st.error(f"Ошибка при размещении ордера: {str(e)}")
                    
        # Текущие позиции
        try:
            positions = trader.get_positions()
            if positions:
                st.subheader("Текущие позиции")
                for pos in positions:
                    st.info(f"{pos.symbol}: {pos.qty} шт. | Текущая цена: ${pos.current_price}")
        except Exception as e:
            st.error(f"Ошибка получения позиций: {str(e)}")

# Основной интерфейс
if st.session_state.run_analysis:
    try:
        with st.spinner("Загрузка данных..."):
            data = load_data(ticker, period, interval)
            
        if data.empty:
            st.warning("Нет данных для отображения. Проверьте параметры и попробуйте снова.")
        else:
            # Добавляем технические индикаторы
            data = add_technical_indicators(data)
            
            # Основные метрики
            if len(data) > 1:
                last_close = data['Close'].iloc[-1].item()
                prev_close = data['Close'].iloc[-2].item()
                change_pct = round(((last_close - prev_close) / prev_close * 100), 2)
            else:
                last_close = data['Close'].iloc[0].item() if len(data) == 1 else 0
                change_pct = 0
                st.warning("Мало данных для расчета изменения цены")
            
            st.success(f"Данные загружены | {ticker} | {period} | {interval}")
            
            if last_close > 0:
                metric_col1, metric_col2 = st.columns(2)
                metric_col1.metric("Текущая цена", f"{last_close:.2f}")
                metric_col2.metric("Изменение", f"{change_pct}%", 
                                  delta_color="inverse" if change_pct < 0 else "normal")
            
            # Графики
            if not data.empty and len(data) > 1:
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
                    
                    if 'SMA20' in data.columns:
                        fig.add_trace(go.Scatter(
                            x=data.index,
                            y=data['SMA20'],
                            name='SMA 20',
                            line=dict(color='blue', width=2)
                        ))
                    
                    if 'SMA50' in data.columns:
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
                    
                    if 'RSI' in data.columns:
                        st.subheader("Индикатор RSI")
                        rsi_fig = go.Figure()
                        rsi_fig.add_trace(go.Scatter(
                            x=data.index,
                            y=data['RSI'],
                            name='RSI',
                            line=dict(color='purple', width=2)
                        ))
                        rsi_fig.add_hline(y=30, line_dash="dash", line_color="green")
                        rsi_fig.add_hline(y=70, line_dash="dash", line_color="red")
                        rsi_fig.update_layout(height=300)
                        st.plotly_chart(rsi_fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Ошибка построения графика: {str(e)}")
            
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
        if 'data' in locals():
            st.write(f"Количество строк: {len(data)}")
            st.write(f"Колонки: {data.columns.tolist()}")
            if not data.empty:
                st.write("Последние 5 строк:")
                st.write(data.tail())
else:
    st.info("Задайте параметры и нажмите 'Обновить данные'")
    st.image("https://via.placeholder.com/800x400?text=График+появится+после+загрузки", 
             caption="Пример интерфейса")

# Дополнительный раздел для Paper Trading
if alpaca_available and st.session_state.run_analysis:
    st.divider()
    st.header("📊 Управление Paper Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            st.subheader("История ордеров")
            orders = trader.get_orders(status='all')[:5]
            if orders:
                order_data = []
                for order in orders:
                    order_data.append({
                        "ID": order.id,
                        "Символ": order.symbol,
                        "Тип": order.side,
                        "Статус": order.status,
                        "Количество": order.qty,
                        "Цена": f"${order.filled_avg_price}" if order.filled_avg_price else "-"
                    })
                st.dataframe(pd.DataFrame(order_data))
            else:
                st.info("Нет истории ордеров")
        except Exception as e:
            st.error(f"Ошибка получения истории ордеров: {str(e)}")
            
    with col2:
        try:
            st.subheader("Доступные средства")
            account = trader.get_account()
            st.metric("Баланс счета", f"${account.equity}")
            st.metric("Доступные для торговли", f"${account.buying_power}")
            st.metric("Валюта", account.currency)
            
            if st.button("Закрыть все позиции", type="secondary"):
                try:
                    trader.close_all_positions()
                    st.success("Все позиции успешно закрыты!")
                except Exception as e:
                    st.error(f"Ошибка при закрытии позиций: {str(e)}")
        except Exception as e:
            st.error(f"Ошибка получения информации о счете: {str(e)}")