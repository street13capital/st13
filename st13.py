"""Python package for trend analysis"""
# MIT License, Copyright 2025 Street 13 Capital Ltd
# https://github.com/street13capital/st13/blob/main/LICENSE
__version__ = '0.6.0'

import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import mplfinance as mpf
import sys

def mplfinance_candlestick_log(df, title="Candlestick Chart (log scale)", timeframe='daily'):
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
        title += " weekly chart"
    elif timeframe.lower() == 'monthly':
        df_clean = resample_to_monthly(df_clean)
        title += " monthly chart"

    # define number of trendlines to draw to focus on dominant lines
    lines_to_draw = 3
    
    # window to check for local minima and maxima, must be odd number
    reversal_window = 5
    
    # threshold to consider reversal point as part of the same line
    noise_threshold = 0.05
    
    # lists to store the reversal points
    bottoming_points = []
    topping_points = []
    
    # list of predefined window size
    previous_points = []
    
    for index, row in df_clean.iterrows():
        # append new point to the consideration window
        previous_points.append([index, row['Close']])
    
        # maintain window size by removing oldest point
        if len(previous_points) > reversal_window:
            previous_points.pop(0)
    
        # only start checking when window is populated
        if len(previous_points) >= reversal_window:
            topping_point = True
            bottoming_point = True
            starting_position = ((reversal_window - 1) // 2)
            for n in range(reversal_window):
                if previous_points[n][1] > previous_points[starting_position][1]:
                    topping_point = False
                if previous_points[n][1] < previous_points[starting_position][1]:
                    bottoming_point = False
            if topping_point:
                topping_points.append([previous_points[starting_position][0], previous_points[starting_position][1]])
            if bottoming_point:
                bottoming_points.append([previous_points[starting_position][0], previous_points[starting_position][1]])
    
    reversal_points = topping_points + bottoming_points
    weighted_reversal_points = []
    
    for n in range(len(reversal_points)):
        reference_weight = 0
        reference_value = reversal_points[n][1]
        for m in range(len(reversal_points)):
            if (abs(reference_value - reversal_points[m][1])/reference_value) <= noise_threshold:
                reference_weight += 1
        weighted_reversal_points.append([reference_value, reference_weight])
    
    weighted_reversal_points.sort(key=lambda x: x[1], reverse=True)
    
    lines_already_drawn = 0
    lines_coefficients = []
    
    for n in range(len(weighted_reversal_points)):
        reversal_clusters = []
        # stop if there is only 1 reversal point for line
        if weighted_reversal_points[n][1] == 1:
            break
        reference_value = weighted_reversal_points[n][0]
        for m in range(len(weighted_reversal_points)):
            if (abs(reference_value - weighted_reversal_points[m][0])/reference_value) <= noise_threshold:
                reversal_clusters.append(weighted_reversal_points[m][0])
        cluster_best_value = linear_regression_line(reversal_clusters)
        if len(lines_coefficients) == 0:
            lines_coefficients.append(cluster_best_value)
            lines_already_drawn += 1
        else:
            line_already_exists = False
            for o in range(len(lines_coefficients)):
                if (abs(cluster_best_value - lines_coefficients[o])/cluster_best_value) <= 2 * noise_threshold:
                    line_already_exists = True
            if not line_already_exists:
                lines_coefficients.append(cluster_best_value)    
                lines_already_drawn += 1
    
        if lines_already_drawn == lines_to_draw:
            break

    # Ensure column names are exactly what mplfinance expects
    # mplfinance is case-sensitive and expects specific columns
    ohlc_data = df_clean[required_cols].copy()

    # Create custom chart format, colour, style and plot chart
    mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle='-', y_on_right=False)
    fig, ax = mpf.plot(ohlc_data, 
                       type='candle',
                       style=s,
                       title=title,
                       ylabel='',
                       volume=False,
                       datetime_format='%Y %b',
                       xrotation=30,
                       hlines=dict(hlines=lines_coefficients, colors=['orange'], linestyle='-', linewidths=1),
                       # alines=dict(alines=[[('2020-08-30', 130),('2025-06-30', 258)], [('2020-08-30', 99),('2025-06-30', 197)]], colors=['blue'], linestyle='-', linewidths=1),
                       returnfig=True,
                       figsize=(14, 8))
    
    # Set y-axis to log scale
    ax[0].set_yscale('log')

    # Custom y-axis for better readability
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
    ME means month end as resampling parameter
    """
    monthly_data = df.resample('ME').agg({
        'Open': 'first',    # First open of the month
        'High': 'max',      # Highest high of the month
        'Low': 'min',       # Lowest low of the month
        'Close': 'last',    # Last close of the month
        'Volume': 'sum' if 'Volume' in df.columns else 'first'  # Sum volume if available
    }).dropna()
    
    return monthly_data

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
    for val in [1.5, 3, 6, 7, 15, 30, 60, 70, 150, 300, 700, 1500]:
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
            return f'{x/1000:.0f}k'
        elif x >= 1:
            return f'{x:.0f}'
        else:
            return f'{x:.2f}'
    
    ax.yaxis.set_major_formatter(FuncFormatter(price_formatter))
    
    return ax

# take list of points and find best fit
def linear_regression_line(clusters):
    best_value = 0
    lowest_error = 999999999
    for n in range(len(clusters)):
        error_value = 0
        reference_value = clusters[n]
        for m in range(len(clusters)):
            error_value += (reference_value - clusters[m]) ** 2
        if error_value < lowest_error:
            lowest_error = error_value
            best_value = reference_value
    return best_value

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            # take in asset symbol on Yahoo Finance
            ticker = sys.argv[1]
        else:
            # default to Apple for demonstration
            ticker = "AAPL"

        # Download price data from Yahoo Finance
        df_real = yf.download(ticker, start="2020-01-01", end="2025-06-21", auto_adjust=True)
        
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
        raise ValueError(f"Error downloading {ticker} price data from Yahoo Finance")

    try:
        # plot with mplfinance (requires: pip install mplfinance)
        fig = mplfinance_candlestick_log(df.copy(), ticker, timeframe='monthly')

        plt.show()
        
    except ImportError:
        print("mplfinance not installed. Run: pip install mplfinance")
    except Exception as e:
        print(f"Error with mplfinance: {e}")

