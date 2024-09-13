import yfinance as yf
import time

target_tickers = ['AAPL', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AMAT', 'AMD', 'ANSS', 'ARM', 'ASML', 'AVGO', 'CDNS', 'CRWD', 'CTSH', 'DDOG', 'EA', 'FTNT', 'GFS', 'GOOG', 'GOOGL', 'INTC', 'INTU', 'KLAC', 'LRCX', 'MCHP', 'MDB', 'META', 'MRVL', 'MSFT', 'MU', 'NVDA', 'NXPI', 'ON', 'PANW', 'QCOM', 'SNPS', 'TEAM', 'TTD', 'TTWO', 'TXN', 'WDAY', 'ZS']

target_y_axis = 'trailingPE'

start_time = time.time()

from yahooquery import Ticker

all_symbols = " ".join(target_tickers)
myInfo = Ticker(all_symbols)
myDict = myInfo.price

for ticker in target_tickers:
    ticker = str(ticker)
    longName = myDict[ticker]['longName']
    market_cap = myDict[ticker]['marketCap']
    price = myDict[ticker]['regularMarketPrice']
    print(ticker, longName, market_cap, price)


end_time = time.time()
run_time = round((end_time - start_time), 2)
print(f"All tickers run time: {run_time}")

''' New code '''
start_time = time.time()
prices_dict = {}
# stock_info = yf.Ticker('AAPL AMZN MSFT TSLA NVDA META')

string_tickers = " ".join(target_tickers)

tickers = yf.Tickers(string_tickers)

# print("New\n", tickers.tickers)

for t in tickers.tickers:
    stock_info = tickers.tickers[t].info

    market_cap = stock_info.get('marketCap', 0)
    market_cap_billions = round(market_cap / 1000000000, 2)
    sector = stock_info.get('sector', 'Unknown')
    
    data = {
        'market_cap': market_cap,
        'market_cap_billions': market_cap_billions,
        'str_market_cap_billions': f'{market_cap_billions / 1000}T' if market_cap_billions > 1000 else f'{market_cap_billions}B',
        'market_cap_radius': round(market_cap_billions, 2),
        'beta': stock_info.get('beta', 0),
        'sector': sector,
        target_y_axis: round(stock_info.get(target_y_axis, 0), 2)
    }
    prices_dict[t] = data

# print("New\n", prices_dict)

try:
    end_time = time.time()
    run_time = end_time - start_time
    pace = run_time
    print(f"New way run time: {run_time}")
# Average before refactoring is ~0.08 seconds per stock
except:
    print("No values to calculate pace")


'''Old way'''
start_time = time.time()
prices_dict = {}

for t in target_tickers:
    
    # Get stock price
    stock_info = yf.Ticker(t).info

    # print("OG\n", stock_info)

    market_cap = stock_info.get('marketCap', 0)
    market_cap_billions = round(market_cap / 1000000000, 2)
    sector = stock_info.get('sector', 'Unknown')
    
    data = {
        'market_cap': market_cap,
        'market_cap_billions': market_cap_billions,
        'str_market_cap_billions': f'{market_cap_billions / 1000}T' if market_cap_billions > 1000 else f'{market_cap_billions}B',
        'market_cap_radius': round(market_cap_billions, 2),
        'beta': stock_info.get('beta', 0),
        'sector': sector,
        target_y_axis: round(stock_info.get(target_y_axis, 0), 2)
    }
    prices_dict[t] = data

# print("OG\n", prices_dict)

try:
    end_time = time.time()
    run_time = end_time - start_time
    pace = run_time
    print(f"Old way run time: {run_time}")
# Average before refactoring is ~0.08 seconds per stock
except:
    print("No values to calculate pace")



