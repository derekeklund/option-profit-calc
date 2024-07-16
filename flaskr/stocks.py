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

    # Dictionary of stock market caps and sectors
    prices_dict = {}

    # tickers = ['AMZN', 'AAPL', 'NVDA', 'FSLR']

    tickers = ['AAPL', 'AMZN', 'GOOG', 'TSLA', 'AMD', 'MSFT', 'META', 'NVDA', 'FSLR']

    # Get list of all tickers in company_info table that are in the technology sector
    db = get_db()
    tech_tickers = db.execute(
        'SELECT ticker FROM company_info WHERE sector = "Technology"'
    ).fetchall()

    print("# of tech tickers: ", len(tech_tickers))

    for t in tickers:
            
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

            prices_dict[t]['market_cap_radius'] = round((prices_dict[t]['market_cap_billions']/100), 2)

            # If the radius is too small, make it big enough to see
            if prices_dict[t]['market_cap_radius'] < 3:
                prices_dict[t]['market_cap_radius'] = 3


            prices_dict[t]['sector'] = stock_info['sector']
            prices_dict[t]['pe_ratio'] = round(stock_info['trailingPE'], 2)


    labels = []
    values = []

    x_axis_incrementer = 10

    # Loop over dict
    for key, value in prices_dict.items():
        # print(key, value)

        # Labels for bubbles
        labels.append(key)

        # Space the bubbles out on the x-axis
        prices_dict[key]['x'] = x_axis_incrementer
        x_axis_incrementer += 10

        # Values for bubbles
        new_value = {
            'x': prices_dict[key]['x'],
            'y': prices_dict[key]['pe_ratio'],
            'r': prices_dict[key]['market_cap_radius']
        }

        values.append(new_value)

    print("Labels: ", labels)
    print("Values: ", values)

    for key, value in prices_dict.items():
        print(key, value)

    return render_template('stocks/bubbles.html', labels=labels, values=values, prices_dict=prices_dict)