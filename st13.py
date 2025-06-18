"""Python package for trend analysis"""
# MIT License, Copyright 2025 Street 13 Capital Ltd
# https://github.com/street13capital/st13/blob/main/LICENSE
__version__ = '0.3.0'

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import mplfinance as mpf
from scipy.signal import argrelextrema
from datetime import datetime, timedelta

def mplfinance_candlestick_log(df, title="Candlestick Chart (Log Scale)", timeframe='daily'):
    """
    Create a candlestick chart with log scale using mplfinance
    timeframe: 'daily', 'weekly', 'monthly'
    """
    
    # Clean and prepare data for mplfinance
    df_clean = df.copy()
    
    # Ensure all OHLC columns exist and are numeric
    required_cols = ['Open', 'High', 'Low', 'Close']
    for col in required_cols:
        if col not in df_clean.columns:
            raise ValueError(f"Missing required column: {col}")
        # Convert to numeric and drop NaN values
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Drop rows with any NaN values in OHLC columns
    df_clean = df_clean.dropna(subset=required_cols)
    
    if len(df_clean) == 0:
        raise ValueError("No valid data remaining after cleaning")
    
    # Resample data to weekly or monthly if requested
    if timeframe.lower() == 'weekly':
        df_clean = resample_to_weekly(df_clean)
        title += " (Weekly)"
    elif timeframe.lower() == 'monthly':
        df_clean = resample_to_monthly(df_clean)
        title += " (Monthly)"
    
    # Ensure column names are exactly what mplfinance expects
    # mplfinance is case-sensitive and expects specific column names
    ohlc_data = df_clean[required_cols].copy()
    
    # Create custom chart format and colour style
    mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle='-', y_on_right=False)
    
    fig, ax = mpf.plot(ohlc_data, 
                       type='candle',
                       style=s,
                       title=title,
                       ylabel='',
                       volume=False,
                       datetime_format='%Y %b',
                       xrotation=45,
                       # hlines=dict(hlines=[10], colors=['red'], linestyle='-', linewidths=2),
                       # alines=dict(alines=[(0, 10, len(ohlc_data) - 1, 30)],
                       # colors=['red'],
                       # linestyle='-',
                       # linewidths=2,
                       # alpha=0.8),
                       returnfig=True,
                       figsize=(14, 8))
    
    # Set y-axis to log scale
    ax[0].set_yscale('log')

    # Use custom formatting for better readability
    price_range = (df_clean['Low'].min() * 0.9, df_clean['High'].max() * 1.1)
    format_log_axis_custom(ax[0], price_range)

    return fig

# Function to resample daily data to weekly
def resample_to_weekly(df):
    """
    Convert daily OHLC data to weekly OHLC data
    Week ends on Friday (standard financial convention)
    """
    weekly_data = df.resample('W-FRI').agg({
        'Open': 'first',    # First open of the week
        'High': 'max',      # Highest high of the week
        'Low': 'min',       # Lowest low of the week
        'Close': 'last',    # Last close of the week
        'Volume': 'sum' if 'Volume' in df.columns else 'first'  # Sum volume if available
    }).dropna()
    
    return weekly_data

# Function to resample daily data to monthly
def resample_to_monthly(df):
    """
    Convert daily OHLC data to monthly OHLC data
    """
    monthly_data = df.resample('ME').agg({
        'Open': 'first',    # First open of the month
        'High': 'max',      # Highest high of the month
        'Low': 'min',       # Lowest low of the month
        'Close': 'last',    # Last close of the month
        'Volume': 'sum' if 'Volume' in df.columns else 'first'  # Sum volume if available
    }).dropna()
    
    return monthly_data

# Sample data generation function
def generate_sample_data(start_price=100, days=100, volatility=0.02):
    """
    Generate sample OHLC data with realistic price movements
    """
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                         periods=days, freq='D')
    
    # Generate random walk with drift
    returns = np.random.normal(0.001, volatility, days)
    prices = [start_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    # Generate OHLC from prices
    data = []
    for i, price in enumerate(prices):
        # Add some intraday volatility
        high = price * (1 + abs(np.random.normal(0, 0.01)))
        low = price * (1 - abs(np.random.normal(0, 0.01)))
        open_price = prices[i-1] if i > 0 else price
        close_price = price
        volume = np.random.randint(1000000, 5000000)
        
        data.append({
            'Open': open_price,
            'High': max(high, open_price, close_price),
            'Low': min(low, open_price, close_price),
            'Close': close_price,
            'Volume': volume
        })
    
    return pd.DataFrame(data, index=dates)

# Additional function for custom y-axis formatting
def format_log_axis_custom(ax, price_range=None):
    """
    Custom formatting for log scale y-axis to show meaningful price levels
    """
    from matplotlib.ticker import FixedLocator, FuncFormatter
    
    if price_range is None:
        # Get current axis limits
        ymin, ymax = ax.get_ylim()
    else:
        ymin, ymax = price_range
    
    # Create custom tick locations - use round numbers that make sense
    # For stock prices, use: 1, 2, 5, 10, 20, 50, 100, 200, 500, etc.
    possible_ticks = []
    
    # Generate sensible tick values
    for base in [1, 2, 5]:
        for exp in range(-2, 5):  # From 0.01 to 10000
            tick_val = base * (10 ** exp)
            if ymin <= tick_val <= ymax:
                possible_ticks.append(tick_val)
    
    # Add some intermediate values if needed
    for val in [1.5, 3, 6, 7, 15, 30, 70, 150, 300, 700, 1500]:
        if ymin <= val <= ymax:
            possible_ticks.append(val)
    
    possible_ticks = sorted(list(set(possible_ticks)))
    
    # Limit number of ticks to avoid crowding
    if len(possible_ticks) > 10:
        step = len(possible_ticks) // 8
        possible_ticks = possible_ticks[::step]
    
    # Set custom ticks
    ax.set_yticks(possible_ticks)
    
    # Format tick labels to show actual values
    def price_formatter(x, pos):
        if x >= 1000:
            return f'{x/1000:.0f}K'
        elif x >= 1:
            return f'{x:.0f}'
        else:
            return f'{x:.2f}'
    
    ax.yaxis.set_major_formatter(FuncFormatter(price_formatter))
    
    return ax


if __name__ == "__main__":
    try:
        # Option 1: Use real data from Yahoo Finance
        # Download real stock data
        ticker = "DB"  # Change to any stock symbol
        df_real = yf.download(ticker, start="2020-01-01", end="2025-06-15")
        
        # Clean the data from yfinance
        # yfinance returns MultiIndex columns, flatten them
        if isinstance(df_real.columns, pd.MultiIndex):
            df_real.columns = df_real.columns.droplevel(1)
        
        # Ensure proper column names
        df_real = df_real.rename(columns={
            'Adj Close': 'Close'  # Use regular Close instead of Adj Close
        })
        
        df = df_real

    except Exception as e:
        # Option 2: Use generated sample data
        print(f"Error downloading real data: {e}")
        print("Using generated sample data")
        df = generate_sample_data(start_price=50, days=500, volatility=0.03)  # More days for weekly

    # 3. mplfinance Weekly Chart (requires: pip install mplfinance)
    try:
        fig3 = mplfinance_candlestick_log(df.copy(), "Price History", timeframe='monthly')

        plt.show()
        
    except ImportError:
        print("mplfinance not installed. Run: pip install mplfinance")
    except Exception as e:
        print(f"Error with mplfinance: {e}")
        print("Skipping mplfinance chart...")
