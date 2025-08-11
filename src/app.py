import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data_loader import load_data, get_current_price
from indicators import add_technical_indicators
from paper_trade import PaperTrader
import time

# Настройки страницы
st.set_page_config(
    page_title="Трейдинг Помощник",
    layout="wide",
    page_icon="💹"
)
st.title("💹 Трейдинг Помощник")

# Инициализация состояния
if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False
    st.session_state.data_loaded = False
    st.session_state.data = pd.DataFrame()
    st.session_state.last_trade_time = 0

# Инициализация PaperTrader
alpaca_available = False
trader = None
try:
    trader = PaperTrader()
    alpaca_available = True
except Exception as e:
    st.error(f"Ошибка инициализации PaperTrader: {str(e)}")

# Сайдбар
with st.sidebar:
    st.header("Настройки")
    ticker = st.text_input("Тикер (AAPL, BTC-USD):", "AAPL")
    
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox("Период", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "max"], index=2)
    with col2:
        interval = st.selectbox("Интервал", ["1m", "5m", "15m", "30m", "1h", "1d"], index=5)
    
    if st.button("Обновить данные", type="primary"):
        st.session_state.run_analysis = True
        st.session_state.data_loaded = False
        
    # Paper Trading раздел
    if alpaca_available:
        st.divider()
        st.header("📊 Paper Trading")
        
        try:
            account = trader.get_account()
            st.success("✅ Подключение к Alpaca успешно")
            st.caption(f"Баланс: ${account.equity} | Валюта: {account.currency}")
        except Exception as e:
            st.error(f"Ошибка подключения: {str(e)}")
        
        with st.form("order_form"):
            st.subheader("Разместить ордер")
            order_symbol = st.text_input("Тикер ордера", ticker)
            order_qty = st.number_input("Количество", min_value=1, max_value=100, value=1)
            order_side = st.radio("Тип операции", ["Buy", "Sell"], index=0)
            
            if st.form_submit_button("Отправить ордер"):
                try:
                    # Проверка времени с последней операции
                    current_time = time.time()
                    if current_time - st.session_state.last_trade_time < 5:
                        st.warning("Пожалуйста, подождите 5 секунд между операциями")
                        st.stop()
                    
                    # Исправление формата для криптовалют
                    if "-" in order_symbol:
                        order_symbol = order_symbol.replace("-", "/")
                        
                    order = trader.place_order(order_symbol, order_qty, order_side)
                    st.success(f"Ордер #{order.id} размещен!")
                    # Сбрасываем состояние данных для обновления
                    st.session_state.data_loaded = False
                    st.session_state.last_trade_time = current_time
                except Exception as e:
                    error_msg = str(e)
                    if "insufficient balance" in error_msg.lower():
                        st.error("Ошибка: Недостаточно средств на счете")
                    elif "wash trade" in error_msg.lower():
                        st.error("Ошибка: Невозможно выполнить операцию из-за конфликта ордеров. Попробуйте позже.")
                    elif "no position" in error_msg.lower():
                        st.error("Ошибка: Нет открытой позиции для продажи")
                    else:
                        st.error(f"Ошибка: {error_msg}")
                    
        try:
            positions = trader.get_positions()
            if positions:
                st.subheader("Текущие позиции")
                for pos in positions:
                    st.info(f"{pos.symbol}: {pos.qty} шт. | Цена: ${pos.current_price}")
        except Exception as e:
            st.error(f"Ошибка получения позиций: {str(e)}")

# Основной интерфейс
if st.session_state.run_analysis and not st.session_state.data_loaded:
    try:
        with st.spinner("Загрузка данных..."):
            data = load_data(ticker, period, interval)
            if not data.empty:
                data = add_technical_indicators(data)
            st.session_state.data = data
            st.session_state.data_loaded = True
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {str(e)}")
        st.session_state.data_loaded = False

if st.session_state.data_loaded:
    data = st.session_state.data
    
    if data.empty:
        st.warning("Нет данных для отображения")
    else:
        # Проверяем наличие необходимых столбцов
        if 'Close' not in data.columns:
            st.error("Данные не содержат цен закрытия")
        else:
            try:
                # Убедимся, что данные не пустые и содержат столбец 'Close'
                if not data.empty and 'Close' in data.columns:
                    # Получаем последние значения закрытия
                    if len(data) >= 2:
                        last_close = data['Close'].iloc[-1].item()
                        prev_close = data['Close'].iloc[-2].item()
                        # Проверка на ноль перед делением
                        if prev_close != 0:
                            change_pct = ((last_close - prev_close) / prev_close * 100)
                            change_pct = round(change_pct, 2)
                        else:
                            change_pct = 0
                    elif len(data) == 1:
                        last_close = data['Close'].iloc[0].item()
                        change_pct = 0
                    else:
                        last_close = 0
                        change_pct = 0
                    
                    st.success(f"Данные загружены | {ticker} | {period} | {interval}")
                    
                    if last_close > 0:
                        col1, col2 = st.columns(2)
                        col1.metric("Текущая цена", f"{last_close:.2f}")
                        col2.metric("Изменение", f"{change_pct}%", 
                                    delta_color="inverse" if change_pct < 0 else "normal")
                    else:
                        st.warning("Нет данных о текущей цене")
                else:
                    st.warning("Недостаточно данных для отображения метрик")
                
                # Графики
                if not data.empty and len(data) > 1 and 'Close' in data.columns:
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
                            fig.add_trace(go.Scatter(x=data.index, y=data['SMA20'], name='SMA 20', line=dict(color='blue', width=2)))
                        if 'SMA50' in data.columns:
                            fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name='SMA 50', line=dict(color='orange', width=2)))
                        
                        fig.update_layout(
                            title=f"{ticker} - Свечной график",
                            height=600,
                            template="plotly_white",
                            xaxis_rangeslider_visible=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        if 'RSI' in data.columns:
                            st.subheader("Индикатор RSI")
                            rsi_fig = go.Figure()
                            rsi_fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='purple', width=2)))
                            rsi_fig.add_hline(y=30, line_dash="dash", line_color="green")
                            rsi_fig.add_hline(y=70, line_dash="dash", line_color="red")
                            rsi_fig.update_layout(height=300)
                            st.plotly_chart(rsi_fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Ошибка построения графика: {str(e)}")
                else:
                    st.warning("Недостаточно данных для построения графика")
                
                # Данные
                with st.expander("📋 Исторические данные"):
                    st.dataframe(data.tail(20).sort_index(ascending=False))
                    
                with st.expander("🔍 Информация о данных"):
                    st.write(f"**Период:** {data.index[0].strftime('%Y-%m-%d')} - {data.index[-1].strftime('%Y-%m-%d')}")
                    st.write(f"**Точек данных:** {len(data)}")
                    st.write(f"**Источник:** Yahoo Finance")
                
            except Exception as e:
                st.error(f"Ошибка обработки данных: {str(e)}")
else:
    st.info("Задайте параметры и нажмите 'Обновить данные'")

# Управление Paper Trading
if alpaca_available and st.session_state.data_loaded:
    st.divider()
    st.header("📊 Управление Paper Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            st.subheader("История ордеров")
            orders = trader.get_orders()
            if orders:
                orders_list = []
                for o in orders:
                    # Преобразуем UUID в строку для корректной сериализации
                    orders_list.append({
                        "ID": str(o.id),
                        "Символ": o.symbol,
                        "Тип": o.side,
                        "Статус": o.status,
                        "Кол-во": o.qty,
                        "Цена": f"${o.filled_avg_price}" if o.filled_avg_price else "-"
                    })
                
                # Создаем DataFrame только если есть данные
                if orders_list:
                    orders_df = pd.DataFrame(orders_list)
                    st.dataframe(orders_df)
                else:
                    st.info("Нет истории ордеров")
            else:
                st.info("Нет истории ордеров")
        except Exception as e:
            st.error(f"Ошибка получения истории ордеров: {str(e)}")
            st.info("Проверьте подключение к Alpaca")
            
    with col2:
        try:
            st.subheader("Счет")
            account = trader.get_account()
            st.metric("Баланс", f"${account.equity}")
            st.metric("Доступные средства", f"${account.buying_power}")
            st.caption(f"Валюта: {account.currency}")
            
            # Предупреждение для криптовалют
            if "-" in ticker:
                st.warning("Для торговли криптовалютами требуется счет в USD")
            
            if st.button("Закрыть все позиции", type="secondary"):
                try:
                    # Проверка времени с последней операции
                    current_time = time.time()
                    if current_time - st.session_state.last_trade_time < 5:
                        st.warning("Пожалуйста, подождите 5 секунд между операциями")
                        st.stop()
                    
                    trader.close_all_positions()
                    st.success("Позиции закрыты!")
                    # Сбрасываем состояние данных для обновления
                    st.session_state.data_loaded = False
                    st.session_state.last_trade_time = current_time
                except Exception as e:
                    error_msg = str(e)
                    if "wash trade" in error_msg.lower():
                        st.error("Ошибка: Невозможно закрыть позицию из-за конфликта ордеров. Попробуйте позже.")
                    else:
                        st.error(f"Ошибка: {error_msg}")
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")