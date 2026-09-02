import os
import requests
import pandas as pd
import yfinance as yf

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')


def send_telegram_message(message):
  url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
  payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
  try:
    requests.post(url, json=payload)
  except Exception as e:
    print('Telegram error:', e)


symbol = 'BTC-USD'
df = yf.download(symbol, period='5d', interval='1h', progress=False)
if isinstance(df.columns, pd.MultiIndex):
  df.columns = df.columns.get_level_values(0)
df = df.dropna()

df['Date'] = df.index.date
today = df['Date'].iloc[-1]
today_df = df[df['Date'] == today]

if len(today_df) >= 3:
  ref_low = today_df.iloc[0]['Low']
  latest_row = today_df.iloc[-1]
  prev_row = today_df.iloc[-2]
  current_price = latest_row['Close']
  latest_time = str(today_df.index[-1])

  is_bullish_sweep = (
      prev_row['Low'] < ref_low
      and latest_row['Close'] > latest_row['Open']
      and latest_row['Close'] > ref_low
  )

  if is_bullish_sweep:
    # Risk Management Calculations
    entry_price = current_price
    # Stop loss set kiya hai sweep low ke thoda niche safety buffer ke sath
    stop_loss = min(prev_row['Low'], latest_row['Low']) - 20
    risk = entry_price - stop_loss
    take_profit = entry_price + (risk * 2)  # 1:2 Risk-to-Reward Ratio

    msg = (
        f'🚨 *LIQUIDITY SWEEP BUY SIGNAL!*\n'
        f'━━━━━━━━━━━━━━━━━━━\n'
        f'📌 **Symbol:** {symbol}\n'
        f'🟢 **Entry:** `{entry_price:.2f}`\n'
        f'🛑 **Stop Loss:** `{stop_loss:.2f}`\n'
        f'🎯 **Take Profit:** `{take_profit:.2f}`\n'
        f'⏰ **Time:** {latest_time}\n'
        f'━━━━━━━━━━━━━━━━━━━'
    )
    send_telegram_message(msg)
    print('Bullish sweep signal with SL & TP sent!')
  else:
    print(f'No sweep signal at {latest_time}')
else:
  print('Not enough data for today yet.')
