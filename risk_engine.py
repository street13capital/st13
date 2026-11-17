"""RISK 13 INTRADAY RISK ENGINE FOR METATRADER 5 RUNNING ON MACOS"""
# https://github.com/street13capital/risk13/blob/master/LICENSE
# MIT License, Copyright 2026 苏昭鸣

import os
import csv
import math
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
import time
import sys
import subprocess
import keyring
import mt5_mac as mt5
import tty
import termios
import select
import atexit

# parameters for intraday risk engine

# micro trading option to trade 1/10 size
# for testing and development of engine
micro_trading_enabled = False

# time-based daily risk allocation
# trading window in UTC 24h format
# split risk to different sessions
distributed_daily_risk = True
trading_start_utc_time = '0700'
trading_end_utc_time = '1900'
total_trading_sessions = 3

# enable keys to long, short, close trades
# b = buy (long), n = close, m = sell (short)
# x = emergency flatten and close all positions
# edit watchlist_symbols and selected_trade_symbol
# in the later section below to set what to trade
enable_keys_to_trade = True

# reduce terminal size to fit output
resize_terminal_window = True

# trading capital outside brokerage account
# modify risk_engine.txt last field directly
# below is just to initialise the variable
# to create the initial risk_engine.txt file
capital_park_in_bank = 0

# disable adding of trades to cap risk
disable_adding_trades = True

# cut at fraction of trade risk instead
# as price hit -0.382R before +0.382R
# so it might mean the bias is wrong
enable_tight_cut_loss = True
if enable_tight_cut_loss:
    cut_loss_multiplier = 0.382
else: 
    cut_loss_multiplier = 1.0

# risk limits to flatten positions
trade_risk_percentage = 0.010
daily_risk_percentage = 0.063
weekly_risk_percentage = 0.18
if micro_trading_enabled:
    trade_risk_percentage /= 10
    daily_risk_percentage /= 10
    weekly_risk_percentage /= 10

# show trade size factoring risk limit
display_trade_size = True

# define symbols with their parameters
# - lot size ratio relative to capital
# - point for stop loss at trade risk
# for eg below is 45, 250, 125 points
# pip for forex pairs, points for others
watchlist_symbols = [('EURUSD', 0.000222, 4.5),
                     ('BTCUSD', 0.000040, 250),
                     ('USTEC',  0.000080, 125)]

# set selected symbol from above watchlist
# 0 is the first one, 1 is second one etc
selected_trade_symbol = 1

# define list to track peak profits for symbols
trade_peak_profit = [0] * len(watchlist_symbols)

# load selected trade symbol parameters
default_trade_symbol = watchlist_symbols[selected_trade_symbol][0]
trade_size_constant = watchlist_symbols[selected_trade_symbol][1]
default_stop_loss_pips = watchlist_symbols[selected_trade_symbol][2]
if micro_trading_enabled:
    trade_size_constant /= 10

# stops to limit loss and protect profit

# for eg if price moved +0.382R and goes back,
# exit breakeven to avoid cut at normal cutloss.
# it could be price moved but not working out
# so the entry signal might be invalidated.
breakeven_stop = True
breakeven_setting = 0.382

# profit stops at pre-defined thresholds.
# rationale is if price moved by an amount
# but retraces back instead of continuing,
# it suggests the trend isn't that strong
# to switch to the trailing stop approach.
# the percentage is at how much of target
# after hitting before locking in profits.
# if 1.0 too easily triggered with 1 tick.
profit_stop = True
profit_stop_percentage = 0.786
profit_setting = [0.618, 0.81, 1.0, 1.25]

# if price moved +2.5R, exit positions when
# price retraces 0.5R from the peak profit.
# similarly +4.0R and +6.5R to lock profits,
# trailing even tighter with 0.25R and 0.13R.
# also started trailing at +1.5R to lock profits
# because that is already 4.85x of tight cutloss.
protective_stop = True
protective_setting = [(1.5, 0.3),
                      (2.0, 0.4),
                      (2.5, 0.5),
                      (4.0, 0.25),
                      (6.5, 0.13)]

# how often to check account status
polling_period_in_sec = 0.250

# data file to store capital peaks
risk_data_file = 'risk_engine.txt'

# log intraday equity for viewing
log_intraday_equity = True
display_equity_curve = True

# obviously need to log to display
if display_equity_curve:
    log_intraday_equity = True

# initialise remaining variables
daily_peak_balance = None
weekly_peak_balance = None
last_printout_time = 0
force_subloop_refresh = False
force_refresh_msg = ''

def flatten_all_positions(symbol=None):
    # uncomment return for development during trading
    # so that engine will not wrongly close positions
    # return

    positions = mt5.positions_get(symbol)
    if positions is None or len(positions) == 0:
        return

    for pos in positions:
        if pos.type == mt5.POSITION_TYPE_BUY:
            trade_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(pos.symbol).bid
        else:
            trade_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(pos.symbol).ask

        close_payload = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': pos.symbol,
            'volume': pos.volume,
            'type': trade_type,
            'position': pos.ticket,
            'price': price,
            'deviation': 30,
            'magic': 999999,
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(close_payload)

def open_new_trade(symbol, direction, lot_size, comment='', sl_pips=None, tp_pips=None):
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        return None

    # safeguard in case not in watchlist
    # and API call return execution error
    if not symbol_info.visible:
        mt5.symbol_select(symbol, True)

    # confirm there is price quotation
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return None

    # prepare parameters for API request
    # assume major forex pairs with USD
    # pip calculation vs cent for others
    # can add on here for minors later
    if 'USD' in symbol and symbol != 'BTCUSD':
        pip = symbol_info.point * 10
    else:
        pip = symbol_info.point * 100
    decimal_digits = symbol_info.digits
    is_buy = direction.upper() == 'BUY'
    price = tick.ask if is_buy else tick.bid
    trade_type = mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL
    sl = round(price + (-1 if is_buy else 1) * sl_pips * pip, decimal_digits) if sl_pips else 0.0
    tp = round(price + (1 if is_buy else -1) * tp_pips * pip, decimal_digits) if tp_pips else 0.0

    deal_request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': float(lot_size),
        'type': trade_type,
        'price': price,
        'sl': sl,
        'tp': tp,
        'deviation': 10,
        'magic': 999999,
        'comment': comment,
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(deal_request)

# 1) connect to local MT5 instance running on macOS.
# using python keyring to securely store credentials,
# then continue with other initialisation prepwork.
# terminal path override is needed to work vs the default using \\
windows_terminal_path = 'C:/Program Files/MetaTrader 5/terminal64.exe'
mt5.initialize(path=windows_terminal_path)
mt5_login = int(keyring.get_password('MT5_Account', 'login'))
mt5_password = keyring.get_password('MT5_Account', 'password')
mt5_server = keyring.get_password('MT5_Account', 'server')
mt5.login(mt5_login, mt5_password, mt5_server)

# initial clear screen before printing figures
# and reduce terminal window size if enabled
os.system('cls' if os.name == 'nt' else 'clear')
# optimally reduce terminal size to show status
if resize_terminal_window:
    original_term_size = os.get_terminal_size()
    sys.stdout.write(f'\x1b[8;{9};{27}t')
    sys.stdout.flush()

# below accept key inputs without enter
# and restore original setting on exit
def restore_terminal():
    termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_terminal_settings)
stdin_fd = sys.stdin.fileno()
old_terminal_settings = termios.tcgetattr(stdin_fd)
atexit.register(restore_terminal)
tty.setcbreak(stdin_fd)

# below start command to not let laptop sleep
# but allow display dim while still running
subprocess.Popen(
    ["caffeinate", "-i", "-w", str(os.getpid())],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# calculate trading hours in defined trading window
trading_start_hour = int(trading_start_utc_time[:2])
trading_start_minute = int(trading_start_utc_time[2:])
trading_end_hour = int(trading_end_utc_time[:2])
trading_end_minute = int(trading_end_utc_time[2:])
total_trading_hours = (60 * trading_end_hour + trading_end_minute - \
                       60 * trading_start_hour - trading_start_minute) / 60
trading_hours_per_session = total_trading_hours / total_trading_sessions

# 2) set peak balance from data file or reset balance
# reset if UTC time starts a new day, ie Singapore time 8am
# that is a good reset time at the start of Asia time zone
current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
if os.path.exists(risk_data_file):
    with open(risk_data_file, 'r') as f:
        last_saved_date, last_saved_balance, saved_weekly_balance, \
            saved_capital_in_bank = f.read().strip().split(',')
        weekly_peak_balance = float(saved_weekly_balance)
        capital_park_in_bank = float(saved_capital_in_bank)
        if last_saved_date == current_date:
            daily_peak_balance = float(last_saved_balance)
        else:
            # refresh daily peak balance on new day
            account = mt5.account_info()
            daily_peak_balance = account.balance + capital_park_in_bank
            # refresh weekly peak balance on new week
            if datetime.now(timezone.utc).weekday() == 0:
                weekly_peak_balance = daily_peak_balance
            with open(risk_data_file, 'w') as f:
                f.write(f'{current_date},{daily_peak_balance:.2f},'
                    f'{weekly_peak_balance:.2f},{capital_park_in_bank:.2f}')
else:
    account = mt5.account_info()
    daily_peak_balance = account.balance + capital_park_in_bank
    weekly_peak_balance = daily_peak_balance
    with open(risk_data_file, 'w') as f:
        f.write(f'{current_date},{daily_peak_balance:.2f},'
            f'{weekly_peak_balance:.2f},{capital_park_in_bank:.2f}')

# start equity curve background process before entering loop
if display_equity_curve:
    subprocess.Popen(
        [sys.executable, 'equity_curve.py'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )

# 3) risk engine loop based on polling_period_in_sec
try:
    while True:
        # get latest account figures at every cycle
        account = mt5.account_info()

        # 4) update daily peak balance and store it
        # then calculate daily and weekly risk floors
        if (account.balance + capital_park_in_bank) > daily_peak_balance:
            daily_peak_balance = account.balance + capital_park_in_bank
            if daily_peak_balance > weekly_peak_balance:
                weekly_peak_balance = daily_peak_balance
            with open(risk_data_file, 'w') as f:
                f.write(f'{current_date},{daily_peak_balance:.2f},'
                    f'{weekly_peak_balance:.2f},{capital_park_in_bank:.2f}')

        # 5) only print periodically to reduce cpu usage
        # if enabled, log intraday equity periodically
        current_time = time.monotonic()
        if ((current_time - last_printout_time) >= 30) or force_subloop_refresh:
            # update counter for next loop cycle
            last_printout_time = current_time
            # reset force refresh of this subloop
            force_subloop_refresh = False
            # print risk notice once per print cycle
            risk_exceeded_printed = False

            # risk floor calculation can skip main loop and do every 30 seconds
            # possible that within 30 seconds a big move happened and reversed
            # but that would be caught by the trade risk and different stops
            # without the new daily risk floor triggered for this edge case
            if not distributed_daily_risk:
                daily_risk_floor = (1 - daily_risk_percentage) * daily_peak_balance
                weekly_risk_floor = (1 - weekly_risk_percentage) * weekly_peak_balance
            else:
                # first check which trading session is the time now
                # then calculate risk floors to allocate risk capital
                current_time = datetime.now(timezone.utc)
                elapsed_trading_hours = (60 * current_time.hour + current_time.minute - \
                                        60 * trading_start_hour - trading_start_minute) / 60
                if elapsed_trading_hours < 0:
                    elapsed_trading_hours = 0 # handle session starting earlier
                limit_percentage = (elapsed_trading_hours + trading_hours_per_session) \
                                   // trading_hours_per_session / total_trading_sessions
                limit_percentage = min(limit_percentage, 1.0) # handle session ending later
                daily_risk_floor = (1 - limit_percentage * daily_risk_percentage) \
                                   * daily_peak_balance
                weekly_risk_floor = (1 - weekly_risk_percentage) * weekly_peak_balance

            # calculate and display trade size for next trade
            # accounting for remaining daily risk for next trade
            # calculate even when not displaying to place trades
            available_risk_capital = (account.equity + capital_park_in_bank) - \
                                        max(daily_risk_floor, weekly_risk_floor)
            trade_risk_capital = trade_risk_percentage * daily_peak_balance
            next_trade_size = trade_size_constant * (account.equity + capital_park_in_bank)
            if available_risk_capital <= 0:
                next_trade_size = 0
            elif available_risk_capital < trade_risk_capital:
                next_trade_size = next_trade_size * available_risk_capital / trade_risk_capital
            if display_trade_size:
                trade_size_text = '\nSize:    ' + f'{Decimal(f'{next_trade_size:.2g}'):f}' + '\n'
            else:
                trade_size_text = '\n'

            # use special code to clear screen not slower OS I/O
            print('\033[H\033[J[Risk 13 - ' + default_trade_symbol + ']' + \
                '\nMaximum:', f'{daily_peak_balance:.2f}',
                '\nCurrent:', f'{account.balance + capital_park_in_bank:.2f}',
                '\nEquity: ', f'{account.equity + capital_park_in_bank:.2f}',
                '\nP&L:    ', f'{account.profit:.2f}', trade_size_text, force_refresh_msg)
            force_refresh_msg = ''

            if log_intraday_equity:
                with open('equity_curve.txt', mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'), 
                        round(account.equity + capital_park_in_bank, 2)
                    ])

        # 6) check if trades exceeded trades risk limit
        # then flatten all open positions to force close
        # this effectively acts as stop loss at trade limit
        for trade_symbol in watchlist_symbols:
            positions = mt5.positions_get(trade_symbol[0])
            if positions is None or len(positions) == 0:
                pass
            else:
                symbol_total_profit = 0
                for pos in positions:
                   symbol_total_profit += pos.profit
                if symbol_total_profit < (-trade_risk_percentage * \
                cut_loss_multiplier * daily_peak_balance):
                    flatten_all_positions(trade_symbol[0])
                    print('[TRADE RISK EXCEEDED]')

        # 7) check if equity exceeded daily risk limit
        # then flatten all open positions if there is any
        if weekly_risk_floor > daily_risk_floor:
            if (account.equity + capital_park_in_bank) < weekly_risk_floor:
                flatten_all_positions()
                if not risk_exceeded_printed:
                    risk_exceeded_printed = True
                    print('[WEEKLY RISK EXCEEDED]')

        elif (account.equity + capital_park_in_bank) < daily_risk_floor:
            flatten_all_positions()
            if not risk_exceeded_printed:
                risk_exceeded_printed = True
                if distributed_daily_risk:
                    print('[SESSION RISK EXCEEDED]')
                else:
                    print('[DAILY RISK EXCEEDED]')

        # 8) breakeven and protective stops to limit loss and protect profit
        trade_risk_amount = trade_risk_percentage * daily_peak_balance
        for index, trade_symbol in enumerate(watchlist_symbols): 
            positions = mt5.positions_get(trade_symbol[0])
            if positions is None or len(positions) == 0:
                trade_peak_profit[index] = 0
            else:
                symbol_total_profit = 0
                for pos in positions:
                   symbol_total_profit += pos.profit
                if symbol_total_profit > trade_peak_profit[index]:
                    trade_peak_profit[index] = symbol_total_profit
                positions_already_flattened = False

                if breakeven_stop and (symbol_total_profit <= 0) and \
                (trade_peak_profit[index] >= (breakeven_setting * trade_risk_amount)):
                    flatten_all_positions(trade_symbol[0])
                    positions_already_flattened = True
                    print('[BREAKEVEN TRIGGERED]')

                if profit_stop and not positions_already_flattened:
                    for threshold in profit_setting:
                        if (trade_peak_profit[index] >= (threshold * trade_risk_amount)) \
                        and (symbol_total_profit \
                        <= (profit_stop_percentage * threshold * trade_risk_amount)):
                            flatten_all_positions(trade_symbol[0])
                            positions_already_flattened = True
                            print(f'[{threshold}R STOP TRIGGERED]')
                            break

                if protective_stop and not positions_already_flattened:
                    for threshold in protective_setting:
                        if (trade_peak_profit[index] >= (threshold[0] * trade_risk_amount)) \
                        and (symbol_total_profit \
                        <= (trade_peak_profit[index] - (threshold[1] * trade_risk_amount))):
                            flatten_all_positions(trade_symbol[0])
                            print(f'[{threshold[0]}R STOP TRIGGERED]')
                            break

        # 9) handle pre-defined keys to place or close trades
        # will wait up to polling_period_in_sec delay but
        # immediately execute on keypress detected 
        if enable_keys_to_trade:
            key_ready, _, _ = select.select([sys.stdin], [], [], polling_period_in_sec)
            if key_ready:
                key_pressed = sys.stdin.read(1).lower()
                if default_trade_symbol != 'USTEC':
                    lot_size = float(Decimal(str(next_trade_size)).quantize(Decimal('0.01'), \
                        rounding=ROUND_DOWN))
                else:
                    lot_size = float(Decimal(str(next_trade_size)).quantize(Decimal('0.1')))

                if key_pressed == 'x':
                    flatten_all_positions()
                    print('[CLOSE ORDER SENT]')
                elif key_pressed == 'n':
                    flatten_all_positions(default_trade_symbol)
                    print('[CLOSE ORDER SENT]')
                elif key_pressed == 'b':
                    positions = mt5.positions_get(default_trade_symbol)
                    if disable_adding_trades and not (positions is None or len(positions) == 0):
                        print('[NO ADDING TRADES]')
                    else:
                        open_new_trade(default_trade_symbol, 'BUY', lot_size, \
                            sl_pips=default_stop_loss_pips)
                        print('[BUY ORDER SENT]')
                elif key_pressed == 'm':
                    positions = mt5.positions_get(default_trade_symbol)
                    if disable_adding_trades and not (positions is None or len(positions) == 0):
                        print('[NO ADDING TRADES]')
                    else:
                        open_new_trade(default_trade_symbol, 'SELL', lot_size, \
                            sl_pips=default_stop_loss_pips)
                        print('[SELL ORDER SENT]')
                elif key_pressed.isdigit():
                    if len(watchlist_symbols) > int(key_pressed):
                        selected_trade_symbol = int(key_pressed)
                        default_trade_symbol = watchlist_symbols[selected_trade_symbol][0]
                        trade_size_constant = watchlist_symbols[selected_trade_symbol][1]
                        default_stop_loss_pips = watchlist_symbols[selected_trade_symbol][2]
                        if micro_trading_enabled:
                            trade_size_constant /= 10
                        # only need force refresh at this branch because trade size calculation
                        # is done in the subloop and needs to recalculate base on new symbol
                        force_refresh_msg = '\n[' + default_trade_symbol + ' SYMBOL SELECTED]'
                        force_subloop_refresh = True
                    else:
                        print('[CHOSEN SYMBOL UNDEFINED]')

        else: 
            # delay anyway avoid useless computation cycles
            time.sleep(polling_period_in_sec)

except KeyboardInterrupt:
    # graceful exit for Control+C to kill risk engine process
    pass

finally:
    # 10) terminate engine process by sending shutdown to MT5
    # resize back terminal window if needed to original size
    if resize_terminal_window:
        sys.stdout.write(f'\x1b[8;{original_term_size.lines};{original_term_size.columns}t')
        sys.stdout.flush()        
    mt5.shutdown()

