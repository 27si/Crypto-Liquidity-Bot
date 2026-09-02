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
    msg = (
        f'🚨 *LIQUIDITY SWEEP BUY SIGNAL!*\nSymbol:'
        f' {symbol}\nPrice: `{current_price:.2f}`\nTime: {latest_time}'
    )
    send_telegram_message(msg)
    print('Bullish sweep signal sent!')
  else:
    print(f'No sweep signal at {latest_time}')
else:
  print('Not enough data for today yet.')
