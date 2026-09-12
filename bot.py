from datetime import datetime, timezone
import os
import numpy as np
import pandas as pd
import requests
import yfinance as yf

# --- TELEGRAM CONFIGURATION (Crypto Bot) ---
TELEGRAM_TOKEN = os.getenv(
    'TELEGRAM_BOT_TOKEN', 'YOUR_CRYPTO_BOT_TOKEN_HERE'
)  # Yahan apna crypto bot token daalein
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '6409092485')
SYMBOL = 'BTC-USD'


def send_telegram_message(message):
  url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
  payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
  try:
    response = requests.post(url, json=payload)
    return response.json()
  except Exception as e:
    print('Telegram error:', e)


def run_crypto_liquidity_bot():
  print(f'Downloading real-time 1h data for {SYMBOL}...')
  df = yf.download(SYMBOL, period='10d', interval='1h', auto_adjust=False)

  if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
  df = df.dropna()

  if len(df) < 50:
    print('Not enough data loaded for Crypto.')
    return

  # --- ATR Calculation for Risk Management ---
  df['ATR'] = (
      (df['High'] - df['Low'])
      .rolling(window=14)
      .mean()
  )

  # --- Liquidity Sweep Logic (1H Swing Levels) ---
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

  # Sweep Conditions with Volume Filter
  bullish_sweep = (
      (latest_row['Low'] < latest_row['Prev_Low'])
      and (current_price > latest_row['Prev_Low'])
      and (latest_row['Volume'] > latest_row['Avg_Volume'])
  )

  bearish_sweep = (
      (latest_row['High'] > latest_row['Prev_High'])
      and (current_price < latest_row['Prev_High'])
      and (latest_row['Volume'] > latest_row['Avg_Volume'])
  )

  signal_found = False
  message_text = ''

  if bullish_sweep:
    signal_found = True
    entry_price = current_price
    stop_loss = entry_price - (
        2.0 * current_atr
    )  # Swing ke liye secure Stop Loss
    risk = entry_price - stop_loss
    take_profit = entry_price + (risk * 2.5)  # 1:2.5 Target

    message_text = (
        f'🚨 *CRYPTO LIQUIDITY SWEEP - LONG SIGNAL* 🚨\n'
        f'━━━━━━━━━━━━━━━━━━━\n'
        f'📌 *Symbol:* {SYMBOL}\n'
        f'🟢 *Direction:* **BUY / LONG**\n'
        f'💰 *Entry Price:* `{entry_price:.2f}`\n'
        f'🛑 *Stop Loss:* `{stop_loss:.2f}`\n'
        f'🎯 *Take Profit:* `{take_profit:.2f}`\n'
        f'⚖️ *Risk/Reward:* 1:2.5\n'
        f'⏰ *Time:* {formatted_time}\n'
        f'━━━━━━━━━━━━━━━━━━━'
    )

  elif bearish_sweep:
    signal_found = True
    entry_price = current_price
    stop_loss = entry_price + (2.0 * current_atr)
    risk = stop_loss - entry_price
    take_profit = entry_price - (risk * 2.5)  # 1:2.5 Target

    message_text = (
        f'🚨 *CRYPTO LIQUIDITY SWEEP - SHORT SIGNAL* 🚨\n'
        f'━━━━━━━━━━━━━━━━━━━\n'
        f'📌 *Symbol:* {SYMBOL}\n'
        f'🔴 *Direction:* **SELL / SHORT**\n'
        f'💰 *Entry Price:* `{entry_price:.2f}`\n'
        f'🛑 *Stop Loss:* `{stop_loss:.2f}`\n'
        f'🎯 *Take Profit:* `{take_profit:.2f}`\n'
        f'⚖️ *Risk/Reward:* 1:2.5\n'
        f'⏰ *Time:* {formatted_time}\n'
        f'━━━━━━━━━━━━━━━━━━━'
    )

  if signal_found:
    send_telegram_message(message_text)
    print('Crypto Liquidity Sweep signal sent successfully!')
  else:
    print(
        f'No liquidity sweep signal for Crypto at {formatted_time}. Current'
        f' Price: {current_price:.2f}'
    )


if __name__ == '__main__':
  run_crypto_liquidity_bot()
    
