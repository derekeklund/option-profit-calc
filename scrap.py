import yfinance as yf
# from datetime import datetime

# Get financial data from ticker
ticker = yf.Ticker('MSFT')

# Get info on the company
info = ticker.info

# print(info) 

for key, value in info.items():
    print(f'{key}: {value}')

# Get trailing pe for the company
beta = info['beta']
print("Beta:", beta)
