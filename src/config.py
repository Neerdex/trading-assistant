import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
        self.ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
        
    def validate(self):
        if not self.ALPACA_API_KEY or not self.ALPACA_SECRET_KEY:
            raise ValueError("Alpaca API keys are missing in .env file")
        return True