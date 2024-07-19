import yfinance as yf
# from datetime import datetime

# Get financial data from ticker
ticker = yf.Ticker('DASH')

# Get info on the company
info = ticker.info

# print(info) 

for key, value in info.items():
    print(f'{key}: {value}')

# Get trailing pe for the company
pe = info['trailingPegRatio']
print(pe)
