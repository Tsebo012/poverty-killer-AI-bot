import time
import threading
from fastapi import FastAPI
import alpaca_trade_api as tradeapi

app = FastAPI()

# Configuration
ALPACA_API_KEY = "YOUR_PAPER_API_KEY"
ALPACA_SECRET_KEY = "YOUR_PAPER_SECRET_KEY"
BASE_URL = "https://paper-api.alpaca.markets"
SYMBOL = "AAPL"

api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, BASE_URL, api_version='v2')

# Bot state tracker
bot_status = {"running": False, "last_action": "Idle"}

def trading_loop():
    while bot_status["running"]:
        try:
            bars = api.get_bars(SYMBOL, timeframe="1Day", limit=50).df
            if len(bars) >= 50:
                bars['SMA_10'] = bars['close'].rolling(window=10).mean()
                bars['SMA_30'] = bars['close'].rolling(window=30).mean()
                latest = bars.iloc[-1]
                previous = bars.iloc[-2]
                
                positions = [p.symbol for p in api.list_positions()]
                is_holding = SYMBOL in positions

                if previous['SMA_10'] < previous['SMA_30'] and latest['SMA_10'] > latest['SMA_30']:
                    if not is_holding:
                        api.submit_order(symbol=SYMBOL, qty=1, side='buy', type='market', time_in_force='gtc')
                        bot_status["last_action"] = f"Bought {SYMBOL} at {latest['close']}"
                elif previous['SMA_10'] > previous['SMA_30'] and latest['SMA_10'] < latest['SMA_30']:
                    if is_holding:
                        api.submit_order(symbol=SYMBOL, qty=1, side='sell', type='market', time_in_force='gtc')
                        bot_status["last_action"] = f"Sold {SYMBOL} at {latest['close']}"
        except Exception as e:
            bot_status["last_action"] = f"Error: {str(e)}"
        
        # Check every 5 minutes
        time.sleep(300)

@app.get("/")
def home():
    return {"status": "Backend is active"}

@app.post("/start")
def start_bot():
    if not bot_status["running"]:
        bot_status["running"] = True
        threading.Thread(target=trading_loop, daemon=True).start()
        return {"message": "Trading bot started successfully."}
    return {"message": "Bot is already running."}

@app.post("/stop")
def stop_bot():
    bot_status["running"] = False
    return {"message": "Trading bot stopped."}

@app.get("/status")
def get_status():
    return bot_status
