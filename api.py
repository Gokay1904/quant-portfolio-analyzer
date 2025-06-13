from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
import requests
import time

app = FastAPI()

ALPHA_VANTAGE_API_KEY = "RBXFKL7NPZBF78I5"  # Buraya kendi API anahtarınızı girin

class DateRange(BaseModel):
    start: str
    end: str

def get_tickers():
    # S&P 500'den örnek birkaç hisse
    return ["AAPL", "MSFT"]

def fetch_data(tickers, start, end):
    valid_tickers = []
    frames = []
    for ticker in tickers:
        url = (
            f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED"
            f"&symbol={ticker}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}"
        )
        try:
            r = requests.get(url)
            data = r.json()
            if "Time Series (Daily)" not in data:
                continue
            df = pd.DataFrame(data["Time Series (Daily)"]).T
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            df = df.loc[(df.index >= pd.to_datetime(start)) & (df.index <= pd.to_datetime(end))]
            if not df.empty:
                close = df["5. adjusted close"].astype(float)
                close.name = ticker
                frames.append(close)
                valid_tickers.append(ticker)
            time.sleep(12)  # Alpha Vantage rate limit (5 istek/dakika)
        except Exception:
            continue
    if frames:
        data = pd.concat(frames, axis=1)
    else:
        data = pd.DataFrame()
    return data, valid_tickers

def calculate_annualized_returns_and_risk(data):
    returns = data.pct_change().dropna()
    mean_daily_returns = returns.mean()
    std_daily_returns = returns.std()
    trading_days = 252
    annual_returns = mean_daily_returns * trading_days
    annual_std_dev = std_daily_returns * np.sqrt(trading_days)
    return annual_returns, annual_std_dev

@app.post("/portfolio")
def get_portfolio(dates: DateRange):
    tickers = get_tickers()
    data, valid_tickers = fetch_data(tickers, dates.start, dates.end)
    if len(valid_tickers) == 0:
        return {"error": "Hiçbir hisse için veri bulunamadı. Lütfen tarih aralığını ve API limitini kontrol edin."}
    annual_returns, annual_std_dev = calculate_annualized_returns_and_risk(data)
    risk_free_rate = 0.02
    sharpe_ratios = ((annual_returns - risk_free_rate) / annual_std_dev).to_dict()
    return {
        "tickers": valid_tickers,
        "annual_returns": annual_returns.to_dict(),
        "annual_std_dev": annual_std_dev.to_dict(),
        "sharpe_ratios": sharpe_ratios
    }