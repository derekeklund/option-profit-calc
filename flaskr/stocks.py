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
from flaskr.helpers import get_watchlist
import numpy as np


@bp.route('/watchlist', methods=('GET', 'POST'))
@login_required
def watchlist():
    print("In watchlist route")

    # Get the user's watchlist
    user_id = g.user['id']
    watchlist = get_watchlist(user_id)

    # Input list of tickers to get prices dict
    def get_prices_dict(watchlist):

        prices_dict = {}

        for t in watchlist:

            # Get SPY stock price
            prices = yf.Ticker(t)

            # Get previous couple day's prices
            historical_prices = prices.history(period="5d", interval="1d")

            # Get latest price, % change, and time (AM/PM format)
            latest_price = historical_prices['Close'].iloc[-1].round(2)
            day_before = historical_prices['Close'].iloc[-2].round(2)

            change = ((latest_price - day_before) * 100 / day_before).round(2)

            # time = historical_prices.index[-1].strftime('%I:%M %p')

            # Add price and percent change to nested dictionary
            prices_dict[t] = {}
            prices_dict[t]['price'] = latest_price
            prices_dict[t]['change'] = change

        return prices_dict

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

        # Defaults for chart
        session['summary_ticker'] = 'SPY'
        session['yfinance_range'] = '1mo'
        selected_time_period = '1 Month'
        yfinance_range = '1mo'
        hist = current_company.history(period=yfinance_range)

        labels = hist.index
        values = hist['Close']

        labels = [str(label.date()) for label in labels]
        values = [value for value in values]

        print("values: ", values)

    
    if request.method == 'POST':
        print("POST method")

        # Get the form keys
        form_keys = request.form.keys()
        form_keys = list(form_keys)

        # Check which action the user took
        if request.form['add-ticker'] != '':
            user_action = 'add_ticker'
        elif 'summary' in form_keys:
            user_action = 'summary'
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

        # Get prices & dates for chart
        hist = current_company.history(period=yfinance_range)
        labels = hist.index
        values = hist['Close']
        labels = [str(label.date()) for label in labels]
        values = [value for value in values]


    return render_template('stocks/watchlist.html', prices_dict=prices_dict,watchlist=watchlist, company_info=company_info, time_periods=time_periods, selected_time_period=selected_time_period, labels=labels, values=values)


@bp.route('/bubbles', methods=('GET', 'POST'))
def bubbles():
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

    # Dictionary of stock market caps and sectors
    prices_dict = {}

    tickers = ['AAPL', 'AMZN', 'GOOG', 'TSLA', 'AMD', 'MSFT', 'META', 'NVDA', 'FSLR']

    # Get all tickers from nasdaq_100 table
    db = get_db()
    nasdaq_100_tickers = db.execute(
        'SELECT ticker FROM nasdaq_100'
    ).fetchall()

    # Convert objects to strings
    nasdaq_100_tickers = [t[0] for t in nasdaq_100_tickers]

    # print("# of nasdaq 100 tickers: ", len(nasdaq_100_tickers))

    # tickers = nasdaq_100_tickers

    # query = f'SELECT ticker FROM company_info WHERE sector = "{selected_sector}"'
    query = f'SELECT ticker FROM company_info WHERE sector = "{selected_sector}" AND ticker IN (SELECT ticker FROM nasdaq_100);'

    # Get list of all tickers in company_info table that are in the technology sector
    db = get_db()
    target_tickers = db.execute(
        query
    ).fetchall()

    target_tickers = [t[0] for t in target_tickers]

    print(f"# of target ({selected_sector}) tickers: ", len(target_tickers))

    for t in target_tickers:
            
        print("Ticker: ", t)
        
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


    labels = []
    values = []

    x_axis_incrementer = 10

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

    print("Sectors: ", sectors)

    indices = ['Nasdaq 100', 'S&P 500', 'Russell 2000']

    if selected_index == 'nasdaq_100':
        selected_index = 'Nasdaq 100'
    elif selected_index == 's_and_p_500':
        selected_index = 'S&P 500'
    elif selected_index == 'russell_2000':
        selected_index = 'Russell 2000'

    # Y-axis options
    y_axis_options = ['P/E Ratio', 'PEG Ratio', 'Revenue Growth']

    # X-axis options
    x_axis_options = ['Sector', 'Market Cap', 'Beta']



    return render_template('stocks/bubbles.html', labels=labels, values=values, prices_dict=prices_dict, sectors=sectors, selected_sector=selected_sector,  indices=indices, selected_index=selected_index, y_axis_options=y_axis_options, selected_y_axis=selected_y_axis, x_axis_options=x_axis_options, selected_x_axis=selected_x_axis)