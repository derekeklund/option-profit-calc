# flask --app flaskr run --debug

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

bp = Blueprint('stocks', __name__)

import yfinance as yf
import pandas as pd
from datetime import datetime
from flaskr.db import get_db
from flaskr.auth import login_required
from flaskr.helpers import get_watchlist, get_prices_dict, login_user
import numpy as np
import time


@bp.route('/watchlist', methods=('GET', 'POST'))
# @bp.route('/watchlist/<ticker>', methods=('GET', 'POST'))
@login_required
def watchlist():
    print("In watchlist route")

    # print("Ticker: ", ticker)

    print("g.user: ", g.user)

    # Get the user's watchlist
    user_id = g.user['id']

    print("User ID: ", user_id)

    # Get user's stock watchlist
    watchlist = get_watchlist(user_id)

    # Get prices for each stock in watchlist
    prices_dict = get_prices_dict(watchlist)

    # Convert time period to yfinance format
    def yfinance_time_period(selected_time_period):
        if selected_time_period == '1 Day':
            return '1d'
        elif selected_time_period == '5 Days':
            return '5d'
        elif selected_time_period == '1 Month':
            return '1mo'
        elif selected_time_period == '3 Months':
            return '3mo'
        elif selected_time_period == '6 Months':
            return '6mo'
        elif selected_time_period == 'YTD':
            return 'ytd'
        elif selected_time_period == '1 Year':
            return '1y'    
        elif selected_time_period == '2 Year':
            return '2y'
        elif selected_time_period == '5 Year':
            return '5y'
        elif selected_time_period == '10 Year':
            return '10y'
        elif selected_time_period == 'Max':
            return 'max'

    
    prices_dict = get_prices_dict(watchlist)

    # Time periods to pass to dropdown
    time_periods = ['1 Day', '5 Days', '1 Month', '3 Months', '6 Months', 'YTD', '1 Year', '2 Year', '5 Year', '10 Year', 'Max']

    
    if request.method == 'GET':
        print("GET method")

        # Defaults for summary
        current_company = yf.Ticker('SPY')
        company_info = current_company.info

        # print("Company info city: ", company_info['city'])

        ''' 
        yfinance intervals:
        “1m”, “2m”, “5m”, “15m”, “30m”, “60m”, “90m”, “1h”, “1d”, “5d”, “1wk”, “1mo”, “3mo”
        '''

        # Defaults for chart
        session['summary_ticker'] = 'SPY'
        session['yfinance_range'] = '1mo'
        selected_time_period = '1 Month'
        yfinance_range = '1mo'
        time_interval = '1h'
        hist = current_company.history(period=yfinance_range, interval=time_interval)

        # Labels for chart x-axis (dates)
        labels = hist.index
        time_format = '%m/%d/%Y'
        labels = [label.strftime(time_format) for label in labels]

        # Values for chart y-axis (prices)
        values = hist['Close']
        values = [value for value in values]

    
    if request.method == 'POST':
        print("POST method")

        # Get the form keys
        form_keys = request.form.keys()
        form_keys = list(form_keys)

        print("Form keys: ", form_keys)

        # Check which action the user took
        if 'summary' in form_keys:
            user_action = 'summary'
        elif request.form['add-ticker'] != '':
            user_action = 'add_ticker'
        elif 'remove-ticker' in form_keys:
            user_action = 'remove_ticker'
        else:
            user_action = 'update_chart'

        print("User action: ", user_action)

        # If the user updated a chart input (time period)
        if user_action == 'update_chart':
            
            # Get selected time period from dropdown
            selected_time_period = request.form['time-period']

            # Convert to yfinance format
            yfinance_range = yfinance_time_period(selected_time_period)

            print(f"Updated selected time: {selected_time_period} ({yfinance_range})")

            # Store yfinance time period in session
            session['yfinance_range'] = yfinance_range

    
        # If the user clicked on a ticker to see the financials
        if user_action == 'summary':

            # Get the ticker that was clicked on from the form
            summary_ticker = request.form['summary']

            # Store the ticker in session
            session['summary_ticker'] = summary_ticker

            print("Updated summary ticker: ", summary_ticker)


        # If the user added a ticker to the watchlist
        if user_action == 'add_ticker':

            # Get the ticker that was clicked on from the form
            added_ticker = request.form['add-ticker']
            added_ticker = added_ticker.upper()

            print("Added ticker: ", added_ticker)

            # Add the ticker to favorites table in database
            error = None

            db = get_db()

            # Check if the ticker is already in the favorites table
            if db.execute(
                'SELECT id FROM favorites WHERE ticker = ? AND user_id = ?', (added_ticker, g.user['id'])
            ).fetchone() is not None:
                error = 'Ticker is already in your watchlist.'

            # If not, add to the favorites table
            if error is not None:
                flash(error)
            else:
                db.execute(
                    'INSERT INTO favorites (ticker, user_id)'
                    ' VALUES (?, ?)',
                    (added_ticker, g.user['id'])
                )
                db.commit()

            # Get updated watchlist and prices dictionary
            watchlist = get_watchlist(user_id)
            prices_dict = get_prices_dict(watchlist)


        # If the user removed a ticker from the watchlist
        elif user_action == 'remove_ticker':

            removed_ticker = request.form['remove-ticker']
            print("removed_ticker: ", removed_ticker)

            db = get_db()
            db.execute(
                'DELETE FROM favorites WHERE ticker = ? AND user_id = ?', (removed_ticker, g.user['id'])
            )
            db.commit()

            # Get updated watchlist and prices dictionary
            watchlist = get_watchlist(user_id)
            prices_dict = get_prices_dict(watchlist)


        # Try to get session yfinance_range if there is one (else, 1mo is default)
        try:
            selected_time_period = request.form['time-period']
            yfinance_range = yfinance_time_period(selected_time_period)
        except:
            yfinance_range = '1mo'
            selected_time_period = '1 Month'

        # Try to get session ticker if there is one (else, SPY is default)
        try:
            summary_ticker = session['summary_ticker']
            
        except:
            summary_ticker = 'SPY'
        
        # Get the company info for summary
        current_company = yf.Ticker(summary_ticker)
        company_info = current_company.info

        print("yfinance_range: ", yfinance_range)

        ''' 
        yfinance intervals:
        “1m”, “2m”, “5m”, “15m”, “30m”, “60m”, “90m”, “1h”, “1d”, “5d”, “1wk”, “1mo”, “3mo”
        '''

        # Default time interval (2 years or more is 1 week)
        time_interval = '1wk'

        if yfinance_range == '1d':
            time_interval = '1m'
        elif yfinance_range == '5d':
            time_interval = '15m'
        elif yfinance_range == '1mo':
            time_interval = '1h'
        elif yfinance_range == '3mo':
            time_interval = '1h'
        elif yfinance_range == '6mo':
            time_interval = '1d'
        elif yfinance_range == 'ytd':
            time_interval = '1d'
        elif yfinance_range == '1y':
            time_interval = '1d'

        # Get prices & dates for chart
        hist = current_company.history(period=yfinance_range, interval=time_interval)
        labels = hist.index
        values = hist['Close']

        # Add time to labels if time_interval is 1-5 days
        if yfinance_range == '1d' or yfinance_range == '5d':
            time_format = '%m/%d %I:%M %p'
            labels = [label.strftime(time_format) for label in labels]
        else:
            labels = [str(label.date()) for label in labels]

        values = [value for value in values]

    # If stock is up during period, color is green, else red
    if values[-1] > values[0]:
        background_color = 'rgba(0, 204, 102, 0.1)'
        border_color = 'rgba(0, 204, 102, 1)'
    else:
        background_color = 'rgba(255, 99, 132, 0.1)'
        border_color = 'rgba(255, 99, 132, 1)'


    # Format company info values for table
    for key, value in company_info.items():

        if type(value) == float:
            # Commas and 2 decimal places for floats
            company_info[key] = "{:,.2f}".format(company_info[key])

        elif type(value) == int:
            # Commas for ints
            company_info[key] = "{:,}".format(company_info[key])

    company_info_items = ['shortName', 'totalRevenue', 'currentPrice', 'trailingPE', 'priceToBook', 'returnOnAssets', 'symbol', 'netIncomeToCommon', 'targetMeanPrice', 'forwardPE', 'debtToEquity', 'operatingCashflow', 'city', 'freeCashflow', 'fiftyTwoWeekLow', 'pegRatio', 'revenuePerShare', 'ebitda', 'sector', 'totalDebt', 'fiftyTwoWeekHigh', 'trailingEps', 'priceToSalesTrailing12Months', 'revenueGrowth', 'industry', 'sharesOutstanding', '52WeekChange', 'forwardEps', 'profitMargins', 'earningsGrowth', 'marketCap', 'returnOnEquity', 'quickRatio', 'beta', 'totalCashPerShare', 'shortPercentOfFloat']

    for item in company_info_items:
        if item not in company_info:
            company_info[item] = '--'

    # Check if there's a market cap key
    if 'marketCap' not in company_info:
        company_info['marketCap'] = '--'

    print("background_color: ", background_color)   
    print("border_color: ", border_color)

    return render_template('stocks/watchlist.html', prices_dict=prices_dict,watchlist=watchlist, company_info=company_info, time_periods=time_periods, selected_time_period=selected_time_period, labels=labels, values=values, background_color=background_color, border_color=border_color)


@bp.route('/bubbles', methods=('GET', 'POST'))
def bubbles():
    start_time = time.time()

    print("In bubbles route")

    # Default dropdown values
    selected_index = 'nasdaq_100'
    selected_sector = 'Technology'
    selected_y_axis = 'P/E Ratio'
    selected_x_axis = 'Sector'

    # Default target metric
    target_y_axis = 'trailingPE'
    target_x_axis = 'sector'

    # If user changes dropdown values, update index and sector
    if request.method == 'POST':
        print("POST method")

        # Get the form keys
        form_keys = request.form.keys()
        form_keys = list(form_keys)

        print("Form keys: ", form_keys)

        # Check if user has entered login info in from this page
        username = None

        try:
            username = request.form['username']
        except:
            pass

        # If yes, log user in + refresh page
        if username != None:
            login_user()

        # Check which action the user took
        if 'index' in form_keys:
            selected_index = request.form['index']
        if 'sector' in form_keys:
            selected_sector = request.form['sector']
        if 'yAxis' in form_keys:
            selected_y_axis = request.form['yAxis']
        if 'xAxis' in form_keys:
            selected_x_axis = request.form['xAxis']


    print("Selected Index: ", selected_index)
    print("Selected Sector: ", selected_sector)
    print("Selected Y-Axis: ", selected_y_axis)
    print("Selected X-Axis: ", selected_x_axis)

    if selected_y_axis == 'P/E Ratio':
        target_y_axis = 'trailingPE'
    elif selected_y_axis == 'PEG Ratio':
        target_y_axis = 'trailingPegRatio'
    elif selected_y_axis == 'Revenue Growth':
        target_y_axis = 'revenueGrowth'
    
    if selected_x_axis == 'Sector':
        target_x_axis = 'sector'
    elif selected_x_axis == 'Market Cap':
        target_x_axis = 'market_cap'
    elif selected_x_axis == 'Beta':
        target_x_axis = 'beta'

    if selected_index == 'Nasdaq 100':
        selected_index = 'nasdaq_100'
    elif selected_index == 'S&P 500':
        selected_index = 's_and_p_500'
    elif selected_index == 'Russell 2000':
        selected_index = 'russell_2000'

    # Dictionary of stock market caps and sectors
    prices_dict = {}

    tickers = ['AAPL', 'AMZN', 'GOOG', 'TSLA', 'AMD', 'MSFT', 'META', 'NVDA', 'FSLR']

    # Get all tickers from nasdaq_100 table
    db = get_db()
    nasdaq_100_tickers = db.execute(
        f'SELECT ticker FROM {selected_index}'
    ).fetchall()

    # Convert objects to strings
    nasdaq_100_tickers = [t[0] for t in nasdaq_100_tickers]

    # print("# of nasdaq 100 tickers: ", len(nasdaq_100_tickers))

    # tickers = nasdaq_100_tickers

    if selected_sector == 'All':
        query = f'SELECT ticker FROM company_info WHERE ticker IN (SELECT ticker FROM {selected_index});'
    else:
        query = f'SELECT ticker FROM company_info WHERE sector = "{selected_sector}" AND ticker IN (SELECT ticker FROM {selected_index});'

    # Get list of all tickers in company_info table that are in the technology sector
    db = get_db()
    target_tickers = db.execute(
        query
    ).fetchall()

    def color_code(sector):
        if sector == 'All':
            return 'rgba(255, 99, 132, 0.5)' # red
        elif sector == 'Industrials':
            return 'rgba(0, 204, 102, 0.5)' # green
        elif sector == 'Real Estate':
            return 'rgba(255, 99, 132, 0.5)' # red
        elif sector == 'Finance':
            return 'rgba(54, 162, 235, 0.5)' # blue
        elif sector == 'Health Care':
            return 'rgba(255, 205, 86, 0.5)' # yellow
        elif sector == 'Consumer Staples':
            return 'rgba(153, 102, 255, 0.5)' # purple
        elif sector == 'Consumer Discretionary':
            return 'rgba(255, 159, 64, 0.5)' # orange
        elif sector == 'Miscellaneous':
            return 'rgba(102, 255, 255, 0.5)' # teal
        elif sector == 'Technology':
            return 'rgba(255, 153, 204, 0.5)' # pink
        elif sector == 'Basic materials':
            return 'rgba(201, 203, 207, 0.5)' # light gray
        elif sector == 'Energy':
            return 'rgba(64, 64, 64, 0.5)' # dark gray
        elif sector == 'Telecommunications':
            return 'rgba(0, 204, 102, 0.5)' # green
        elif sector == 'Utilities':
            return 'rgba(255, 99, 132, 0.5)' # red
        else:
            return 'rgba(0, 0, 0, 0.1)' # black

    target_tickers = [t[0] for t in target_tickers]

    print(f"# of target ({selected_index} {selected_sector}) tickers: ", len(target_tickers))

    bubble_colors = [color_code(selected_sector) for t in target_tickers]

    prices_dict = {}

    # Get stats for each ticker and store in prices_dict
    def get_stats(ticker):
        # print("Getting stats for: ", ticker)
        stock_info = yf.Ticker(ticker).info
        market_cap = stock_info.get('marketCap', 0)
        market_cap_billions = round(market_cap / 1000000000, 2)
        sector = stock_info.get('sector', 'Unknown')
        beta = stock_info.get('beta', 0)
        str_market_cap_billions = f'{market_cap_billions / 1000}T' if market_cap_billions > 1000 else f'{market_cap_billions}B'
        market_cap_radius = round(market_cap_billions, 2)

        data = {
            'market_cap': market_cap,
            'market_cap_billions': market_cap_billions,
            'str_market_cap_billions': str_market_cap_billions,
            'market_cap_radius': market_cap_radius,
            'beta': beta,
            'sector': sector,
            target_y_axis: round(stock_info.get(target_y_axis, 0), 2)
        }

        # print(f"Data for {ticker}: {data}")

        prices_dict[ticker] = data


    from concurrent.futures import ThreadPoolExecutor

    start_time = time.time()

    # Use pooling to speed up yf.Ticker().info calls
    with ThreadPoolExecutor() as executor:
        executor.map(get_stats, target_tickers)

    # print("Prices dict: ", prices_dict)

    end_time = time.time()
    run_time = round((end_time - start_time), 2)
    print(f"Query run time: {run_time}")

    labels = []
    values = []

    x_axis_incrementer = 10

    # FOR LOOP TO SPEED UP
    # Loop over dict
    for key, value in prices_dict.items():
        # print(key, value)

        # Scale the market cap radius by getting square root
        prices_dict[key]['market_cap_radius'] = round(np.sqrt(prices_dict[key]['market_cap_radius']), 2)

        # Labels for bubbles
        labels.append(key)

        if selected_x_axis == 'Sector':
            # Space the bubbles out on the x-axis
            prices_dict[key]['x'] = x_axis_incrementer
            x_axis_incrementer += 10

        elif selected_x_axis == 'Market Cap':
            # Get market cap
            prices_dict[key]['x'] = prices_dict[key]['market_cap_billions']

        elif selected_x_axis == 'Beta':
            # Get the beta
            try:
                prices_dict[key]['x'] = round(prices_dict[key]['beta'], 2)
            except KeyError as e:
                prices_dict[key]['x'] = 0
                print(f'No beta for {key}')

        # Values for bubbles
        new_value = {
            'x': prices_dict[key]['x'],
            'y': prices_dict[key][target_y_axis],
            'r': prices_dict[key]['market_cap_radius']
        }

        values.append(new_value)


    # Get sectors in nasdaq 100 for dropdown
    sectors = db.execute(
        'SELECT DISTINCT sector FROM company_info'
    ).fetchall()

    sectors = [s[0] for s in sectors]

    sectors.append('All')

    # Make 'All' is first in the list, Technology is second, Telecommunications is third, None is last
    sectors.sort(key=lambda x: (x != 'All', x != 'Technology', x != 'Telecommunications'))

    print("Sectors: ", sectors)

    indices = ['Nasdaq 100', 'S&P 500', 'Russell 2000']

    if selected_index == 'nasdaq_100':
        selected_index = 'Nasdaq 100'
    elif selected_index == 's_and_p_500':
        selected_index = 'S+P 500'
    elif selected_index == 'russell_2000':
        selected_index = 'Russell 2000'

    print("Selected index: ", selected_index)

    # Y-axis options
    y_axis_options = ['P/E Ratio', 'PEG Ratio', 'Revenue Growth']

    # X-axis options
    x_axis_options = ['Sector', 'Market Cap', 'Beta']

    try:
        end_time = time.time()
        run_time = end_time - start_time
        pace = run_time / len(values)
        print(f"Bubbles time taken (for {len(values)} stock): {run_time} ({pace}/stock) ")
    # Average before refactoring is ~0.08 seconds per stock
    except:
        print("No values to calculate pace")

    print("Values: ", values)

    # Update values to only be the 'y' value
    # values = [value['y'] for value in values]

    # print("Values: ", values)

    print("labels: ", labels)
    

    return render_template('stocks/bubbles.html', labels=labels, values=values, prices_dict=prices_dict, sectors=sectors, selected_sector=selected_sector,  indices=indices, selected_index=selected_index, y_axis_options=y_axis_options, selected_y_axis=selected_y_axis, x_axis_options=x_axis_options, selected_x_axis=selected_x_axis, bubble_colors=bubble_colors)


@bp.route('/monte_carlo', methods=('GET', 'POST'))
def monte_carlo():
    print("In monte carlo route")

    error = None

    # Pre-selected variables
    initial_sum = 10000
    sim_days = 100
    num_sims = 100
    symbol_1 = 'AAPL'
    symbol_2 = 'MSFT'
    symbol_3 = 'AMZN'

    labels = [symbol_1, symbol_2, symbol_3]
    values = [55, 30, 15]
    colors = [
      'rgb(255, 99, 132)', # red
      'rgb(54, 162, 235)', # blue
      'rgb(255, 205, 86)', # yellow
      'rgba(0, 204, 102)', # green
      'rgba(153, 102, 255)', # purple
      'rgba(255, 159, 64)', # orange
      'rgba(102, 255, 255)', # teal
      'rgba(255, 153, 204)', # pink
      'rgba(201, 203, 207)', # gray
      'rgba(64, 64, 64)' # dark gray
    ]

    field_count = 3

    if request.method == 'POST':
        print("POST method")

        # Get the form keys
        form_keys = request.form.keys()
        form_keys = list(form_keys)

        print("Form keys: ", form_keys)

        # Check if user has entered login info in from this page
        username = None

        try:
            username = request.form['username']
        except:
            pass

        # If yes, log user in + refresh page
        if username != None:
            login_user()
        else:
            # No login info entered, continue with simulation form data

            # Clear values and labels
            values = []
            labels = []

            # Capture the submitted form data
            field_count = int(request.form.get('field_count', 3))  # Default to 3 if not found

            print("Field count: ", field_count)

            initial_sum = int(request.form['initial_sum'])
            sim_days = int(request.form['sim_days'])
            num_sims = int(request.form['num_sims'])

            print("Initial sum: ", initial_sum)
            print("Simulation days: ", sim_days)
            print("Number of simulations: ", num_sims)

            for i in range(1, field_count + 1):
                symbol = request.form.get(f'symbol_{i}').upper()
                alloc = int(request.form.get(f'alloc_{i}'))
                if symbol and alloc:
                    labels.append(symbol)
                    values.append(alloc)

            print("Sum values: ", sum(values))

            if sum(values) != 100:
                error = 'Allocation percentages must add up to 100.'
                flash(error)

                return render_template('stocks/monte-carlo.html', labels=labels, values=values, colors=colors, initial_sum=initial_sum, sim_days=sim_days, num_sims=num_sims, symbol_1=symbol_1, symbol_2=symbol_2, symbol_3=symbol_3, field_count=field_count)
        

    # Create plot and return it

    from matplotlib.figure import Figure
    from io import BytesIO
    import base64
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import datetime as dt
    import yfinance as yf

    # Import data
    def get_data(stocks, start, end):

        # Get closing data for each stock from Yahoo Finance directly
        for stock in stocks:

            data = yf.download(stock, start=start, end=end)

            # Keep only date and close columns
            data = data[['Close']]
            
            # Change close column name to stock name
            data.columns = [stock]

            if stock == stocks[0]:
                stockData = data

            else:
                stockData = pd.concat([stockData, data[stock]], axis=1)

        # Get daily changes
        returns = stockData.pct_change()

        # Calculate mean (daily) returns in a covariance matrix
        meanReturns = returns.mean()

        # Covariance means the relationship between two variables (stocks in this case) and to what extent they change together
        # co - together, variance - change
        covMatrix = returns.cov()

        return meanReturns, covMatrix


    # stockList = ['AAPL', 'MSFT', 'AMZN']
    stockList = labels

    endDate = dt.datetime.now()
    startDate = endDate - dt.timedelta(days=300)

    meanReturns, covMatrix = get_data(stockList, startDate, endDate)

    # weights = np.array([0.55, 0.30, 0.15])
    port_percents = [x/100 for x in values]
    weights = np.array(port_percents)


    ''' Monte Carlo Method '''

    # Define number of simulations
    mc_sims = num_sims

    # Time range in days
    T = sim_days

    # 2d array of 100 days with the mean returns repeated for each day
    meanMatrix = np.full(shape=(T, len(weights)), fill_value=meanReturns)

    # Transpose the matrix
    meanMatrix = meanMatrix.T

    # Portfolio values matrix (100 days x 100 simulations)
    portfolio_sims = np.full(shape=(T, mc_sims), fill_value=0.0)

    initialPortfolio = initial_sum

    for m in range(0, mc_sims):
        # MC loops
        # See 11:20 in the video to see how *Multivariate Normal Distribution* is used and how the *Cholesky Decomposition* to determine the *Lower Triangular Matrix* is used for calculations
        # So we get the sample data from the normal distribution and we correlate them with the covariance matrix with the lower triangle

        Z = np.random.normal(size=(T, len(weights)))

        # Lower triangle
        L = np.linalg.cholesky(covMatrix)

        # Note that dot and inner are similar. See docs
        # dailyReturns = meanMatrix + np.dot(L, Z.T)
        dailyReturns = meanMatrix + np.inner(L, Z)

        # Accumulate the daily returns across the days
        portfolio_sims[:, m] = np.cumprod(np.inner(weights, dailyReturns.T) + 1)*initialPortfolio


    # Generate the figure **without using pyplot**.
    fig = Figure(facecolor='#f0f0f0')
    ax = fig.subplots()
    ax.plot(portfolio_sims)

    # Styling
    ax.set_xlabel('Days')
    ax.set_ylabel('Portfolio Value ($)')
    ax.set_title('Monte Carlo Simulation of a Stock Portfolio')
    ax.set_facecolor('#f0f0f0')
    ax.grid(True)

    # Give y axis thousands separator
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))

    # Add initial line to graph
    ax.axhline(y=initialPortfolio, color='k', linestyle='--', label='Initial Portfolio Value')

    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', dpi=200)

    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    plot = f"<img class='matplotlib-chart' src='data:image/png;base64,{data}'/>"


    print("field_count: ", field_count)

    return render_template('stocks/monte-carlo.html', labels=labels, values=values, colors=colors, initial_sum=initial_sum, sim_days=sim_days, num_sims=num_sims, symbol_1=symbol_1, symbol_2=symbol_2, symbol_3=symbol_3, plot=plot, field_count=field_count)