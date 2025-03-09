import yfinance as yf

ticker = 'AAPL'

# Get option expiration dates for ticker
opt = yf.Ticker(ticker).options
print(opt)