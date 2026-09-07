from datetime import datetime, timezone
import os
import numpy as np
import pandas as pd
import requests
import yfinance as yf

# --- TELEGRAM CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv(
    'TELEGRAM_BOT_TOKEN', '8835024039:AAGQDWpkYPQCf4_iAzZmY2OIHvp5wDLPPmE'
)
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '6409092485')

# Dono symbols ki list jinh par bot nazar rakhega
SYMBOLS = ['BTC-USD', 'GC=F']


def send_telegram_message(message):
  url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
  payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
  try:
    response = requests.post(url, json=payload)
    return response.json()
  except Exception as e:
    print('Telegram error:', e)


def run_liquidity_sweep_bot():
  for symbol in SYMBOLS:
    print(f'Checking Liquidity Sweep for {symbol} on 1h timeframe...')
    df = yf.download(symbol, period='10d', interval='1h', auto_adjust=False)

    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)
    df = df.dropna()

    if len(df) < 50:
      print(f'Not enough data for {symbol}. Skipping...')
      continue

    # --- ATR Calculation for Risk Management ---
    df['ATR'] = (
        (df['High'] - df['Low'])
        .rolling(window=14)
        .mean()
    )

    # --- Liquidity Sweep Logic (Swing Levels) ---
    # Pichle 20 candles ka High aur Low (Key Liquidity Zones)
    df['Prev_High'] = df['High'].shift(1).rolling(window=20).max()
    df['Prev_Low'] = df['Low'].shift(1).rolling(window=20).min()
    df['Avg_Volume'] = df['Volume'].rolling(window=20).mean()
    df = df.dropna()

    # Check Latest Closed Candle (-2 index)
    i = len(df) - 2
    latest_row = df.iloc[i]
    latest_time = df.index[i]
    current_price = latest_row['Close']
    current_atr = latest_row['ATR']

    # Convert time to IST (+5:30)
    if latest_time.tzinfo is not None:
      ist_time = latest_time.tz_convert('Asia/Kolkata')
    else:
      ist_time = latest_time.tz_localize('UTC').tz_convert('Asia/Kolkata')

    formatted_time = ist_time.strftime('%Y-%m-%d %I:%M:%S %p IST')

    # Sweep Conditions:
    # 1. Bullish Sweep (Price ne pichla low toda par wapas upar band ho gayi + High Volume)
    bullish_sweep = (
        (latest_row['Low'] < latest_row['Prev_Low'])
        and (current_price > latest_row['Prev_Low'])
        and (latest_row['Volume'] > latest_row['Avg_Volume'])
    )

    # 2. Bearish Sweep (Price ne pichla high toda par wapas niche band ho gayi + High Volume)
    bearish_sweep = (
        (latest_row['High'] > latest_row['Prev_High'])
        and (current_price < latest_row['Prev_High'])
        and (latest_row['Volume'] > latest_row['Avg_Volume'])
    )

    if bullish_sweep:
      entry_price = current_price
      stop_loss = entry_price - (2.0 * current_atr)  # Swing ke liye thoda bada SL
      risk = entry_price - stop_loss
      take_profit = entry_price + (risk * 2.5)

      message_text = (
          f'🚨 *LIQUIDITY SWEEP BUY SIGNAL* 🚨\n'
          f'━━━━━━━━━━━━━━━━━━━\n'
          f'📌 *Symbol:* {symbol}\n'
          f'🟢 *Direction:* **BUY / LONG (Sweep)**\n'
          f'💰 *Entry Price:* `{entry_price:.2f}`\n'
          f'🛑 *Stop Loss:* `{stop_loss:.2f}`\n'
          f'🎯 *Take Profit:* `{take_profit:.2f}`\n'
          f'⏰ *Time:* {formatted_time}\n'
          f'━━━━━━━━━━━━━━━━━━━'
      )
      send_telegram_message(message_text)
      print(f'Bullish sweep alert sent for {symbol}!')

    elif bearish_sweep:
      entry_price = current_price
      stop_loss = entry_price + (2.0 * current_atr)
      risk = stop_loss - entry_price
      take_profit = entry_price - (risk * 2.5)

      message_text = (
          f'🚨 *LIQUIDITY SWEEP SELL SIGNAL* 🚨\n'
          f'━━━━━━━━━━━━━━━━━━━\n'
          f'📌 *Symbol:* {symbol}\n'
          f'🔴 *Direction:* **SELL / SHORT (Sweep)**\n'
          f'💰 *Entry Price:* `{entry_price:.2f}`\n'
          f'🛑 *Stop Loss:* `{stop_loss:.2f}`\n'
          f'🎯 *Take Profit:* `{take_profit:.2f}`\n'
          f'⏰ *Time:* {formatted_time}\n'
          f'━━━━━━━━━━━━━━━━━━━'
      )
      send_telegram_message(message_text)
      print(f'Bearish sweep alert sent for {symbol}!')
    else:
      print(f'No liquidity sweep found for {symbol} at {formatted_time}.')


if __name__ == '__main__':
  run_liquidity_sweep_bot()
  
