import pandas as pd

def add_technical_indicators(data):
    try:
        if len(data) > 20:
            data['SMA20'] = data['Close'].rolling(window=20).mean()
        
        if len(data) > 50:
            data['SMA50'] = data['Close'].rolling(window=50).mean()
            
        if len(data) > 14:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
        return data
    except Exception as e:
        print(f"Ошибка расчета индикаторов: {str(e)}")
        return data