import yfinance as yf
import time

start = time.time()

# Dictionary of stock market caps and sectors
prices_dict = {}

target_tickers = ['AAPL', 'AMZN', 'MSFT', 'TSLA', 'NVDA', 'META']

target_y_axis = 'trailingPE'

for t in target_tickers:
        
    # print("Ticker: ", t)
    
    # Get stock price
    prices = yf.Ticker(t)

    # Get stock info
    stock_info = prices.info

    # Get market cap and sector
    prices_dict[t] = {}
    prices_dict[t]['market_cap'] = stock_info['marketCap']
    prices_dict[t]['market_cap_billions'] = round((prices_dict[t]['market_cap'] / 1000000000), 2)
    
    if prices_dict[t]['market_cap_billions'] > 1000:
        prices_dict[t]['str_market_cap_billions'] = str(prices_dict[t]['market_cap_billions']/1000) + 'T'
    else:
        prices_dict[t]['str_market_cap_billions'] = str(prices_dict[t]['market_cap_billions']) + 'B'

    # prices_dict[t]['market_cap_radius'] = round((prices_dict[t]['market_cap_billions']/100), 2)
    prices_dict[t]['market_cap_radius'] = round((prices_dict[t]['market_cap_billions']), 2)

    # If the radius is too small, make it big enough to see
    # if prices_dict[t]['market_cap_radius'] < 5:
    #     prices_dict[t]['market_cap_radius'] = 5

    # Get beta
    try:
        prices_dict[t]['beta'] = stock_info['beta']
    except KeyError as e:
        prices_dict[t]['beta'] = 0
        print(f'No beta for {t}')


    prices_dict[t]['sector'] = stock_info['sector']

    try:
        prices_dict[t][target_y_axis] = round(stock_info[target_y_axis], 2)
    except:
        # If there is no pe ratio, set it to 0
        prices_dict[t][target_y_axis] = 0

        print(f'No {target_y_axis} for {t}')

print("Time taken: ", time.time() - start)

start = time.time()

for t in target_tickers:
    stock_info = yf.Ticker(t).info
    market_cap = stock_info.get('marketCap', 0)
    market_cap_billions = round(market_cap / 1000000000, 2)
    
    data = {
        'market_cap': market_cap,
        'market_cap_billions': market_cap_billions,
        'str_market_cap_billions': f'{market_cap_billions / 1000}T' if market_cap_billions > 1000 else f'{market_cap_billions}B',
        'market_cap_radius': round(market_cap_billions, 2),
        'beta': stock_info.get('beta', 0),
        'sector': stock_info.get('sector', "Unknown"),
        target_y_axis: round(stock_info.get(target_y_axis, 0), 2)
    }
    prices_dict[t] = data


print("Time taken: ", time.time() - start)