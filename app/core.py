import numpy as np

def calculate_annualized_returns_and_risk(data):
    returns = data.pct_change().dropna()
    mean_daily_returns = returns.mean()
    std_daily_returns = returns.std()
    trading_days = 252
    annual_returns = mean_daily_returns * trading_days
    annual_std_dev = std_daily_returns * np.sqrt(trading_days)
    return annual_returns, annual_std_dev

def calculate_sharpe(returns, risk_free_rate=0.02):
    mean_daily_returns = returns.mean()
    std_daily_returns = returns.std()
    trading_days = 252
    annual_returns = mean_daily_returns * trading_days
    annual_std_dev = std_daily_returns * (trading_days ** 0.5)
    sharpe = (annual_returns - risk_free_rate) / annual_std_dev
    return sharpe