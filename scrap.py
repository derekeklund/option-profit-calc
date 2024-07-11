import yfinance as yf
# from datetime import datetime

# Get financial data from ticker
ticker = yf.Ticker('MSFT')

# Get last 30 days of prices
hist = ticker.history(period='1mo')

labels = hist.index
values = hist['Close']

labels = [str(label.date()) for label in labels]
values = [value for value in values]

print(labels)
print(values)