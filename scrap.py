import yfinance as yf

# Get financial data from ticker
ticker = yf.Ticker('MSFT')

# print(ticker.info)

for key, value in ticker.info.items():
    print(key, ":", value)


# print business summary
print(ticker.info['longBusinessSummary'])

