# flask --app flaskr run --debug

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

bp = Blueprint('stocks', __name__)

import yfinance as yf
import pandas as pd
from datetime import datetime
import time
from flaskr.db import get_db
from flaskr.auth import login_required
from flaskr.helpers import get_watchlist


# https://ibkrcampus.com/ibkr-quant-news/yfinance-library-a-complete-guide/
# https://www.highcharts.com/docs/index
@bp.route('/watchlist', methods=('GET', 'POST'))
@login_required
def watchlist():
    # print("Watchlist route")

    # Get the user's watchlist
    user_id = g.user['id']
    watchlist = get_watchlist(user_id)

    # Default ticker for chart
    session['summary_ticker'] = 'SPY'

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


    prices_dict = get_prices_dict(watchlist)

    # Just for MSFT atm, get the business summary, etc. 
    current_company = yf.Ticker('SPY')
    company_info = current_company.info

    # Chart stuff
    # Get last 30 days of prices for chart
    hist = current_company.history(period='1mo')

    labels = hist.index
    values = hist['Close']

    labels = [str(label.date()) for label in labels]
    values = [value for value in values]

    # Time periods to pass to dropdown
    time_periods = ['1d', '5d', '1mo', '3mo', '6mo', 'ytd', '1y', '2y', '5y', '10y', 'max']

    
    
    if request.method == 'GET':
        print("GET method")

        # Default time period for GET request chart
        selected_time_period = '1mo'


        return render_template('stocks/watchlist.html', prices_dict=prices_dict,watchlist=watchlist, company_info=company_info, time_periods=time_periods, selected_time_period=selected_time_period, labels=labels, values=values)
    

    if request.method == 'POST':
        print("POST method")

        # Get selected time period from dropdown
        selected_time_period = request.form['time-period']
        print("Selected time period: ", selected_time_period)

        # Get the form keys
        form_keys = request.form.keys()
        form_keys = list(form_keys)

        print("Form keys: ", form_keys)


        if request.form['add-ticker'] != '':
            user_action = 'add_ticker'
        elif 'summary' in form_keys:
            user_action = 'summary'
        elif 'remove-ticker' in form_keys:
            user_action = 'remove_ticker'
        else:
            user_action = 'update_chart'

        print("User action: ", user_action)

        # If the user updated a chart input (time period, etc.)
        if user_action == 'update_chart':

            # Get ticker from session
            summary_ticker = session['summary_ticker']

            # Get the company info
            current_company = yf.Ticker(summary_ticker)
            company_info = current_company.info

            # Get prices for chart
            hist = current_company.history(period=selected_time_period)

            # Get labels and values for chart
            labels = hist.index
            values = hist['Close']
            labels = [str(label.date()) for label in labels]
            values = [value for value in values]


            return render_template('stocks/watchlist.html', prices_dict=prices_dict, watchlist=watchlist, company_info=company_info, time_periods=time_periods, selected_time_period=selected_time_period, labels=labels, values=values,)

        

        # If the user clicked on a ticker to see the financials
        if user_action == 'summary':

            # Get the ticker that was clicked on from the form
            summary_ticker = request.form['summary']

            session['summary_ticker'] = summary_ticker

            # Get the company info
            current_company = yf.Ticker(summary_ticker)
            company_info = current_company.info

            # Get last 30 days of prices for chart
            hist = current_company.history(period='1mo')

            labels = hist.index
            values = hist['Close']

            labels = [str(label.date()) for label in labels]
            values = [value for value in values]


            return render_template('stocks/watchlist.html', prices_dict=prices_dict, watchlist=watchlist, company_info=company_info, time_periods=time_periods, selected_time_period=selected_time_period,labels=labels, values=values)


        # If the user added a ticker to the watchlist
        if user_action == 'add_ticker':

            # Get the ticker that was clicked on from the form
            added_ticker = request.form['add-ticker']
            added_ticker = added_ticker.upper()

            print("added_ticker: ", added_ticker)

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

            watchlist = get_watchlist(user_id)
            prices_dict = get_prices_dict(watchlist)

            # Try to get session ticker if there is one (else, SPY is default)
            try:
                summary_ticker = session['summary_ticker']
                # Get the company info
                current_company = yf.Ticker(summary_ticker)
                company_info = current_company.info
            except:
                summary_ticker = None
                # Get the company info
                current_company = yf.Ticker('SPY')
                company_info = current_company.info

            # Get last 30 days of prices for chart
            hist = current_company.history(period='1mo')

            labels = hist.index
            values = hist['Close']

            labels = [str(label.date()) for label in labels]
            values = [value for value in values]


            return render_template('stocks/watchlist.html', prices_dict=prices_dict, added_ticker=added_ticker, watchlist=watchlist, company_info=company_info, time_periods=time_periods, selected_time_period=selected_time_period, labels=labels, values=values)

        # If the user removed a ticker from the watchlist
        elif user_action == 'remove_ticker':

            removed_ticker = request.form['remove-ticker']
            print("removed_ticker: ", removed_ticker)

            db = get_db()
            db.execute(
                'DELETE FROM favorites WHERE ticker = ? AND user_id = ?', (removed_ticker, g.user['id'])
            )
            db.commit()

            watchlist = get_watchlist(user_id)
            prices_dict = get_prices_dict(watchlist)

            # Try to get session ticker if there is one (else, SPY is default)
            try:
                summary_ticker = session['summary_ticker']
                # Get the company info
                current_company = yf.Ticker(summary_ticker)
                company_info = current_company.info
            except:
                summary_ticker = None
                # Get the company info
                current_company = yf.Ticker('SPY')
                company_info = current_company.info

            # Get last 30 days of prices for chart
            hist = current_company.history(period='1mo')

            labels = hist.index
            values = hist['Close']

            labels = [str(label.date()) for label in labels]
            values = [value for value in values]


            return render_template('stocks/watchlist.html', prices_dict=prices_dict,watchlist=watchlist, company_info=company_info, time_periods=time_periods, selected_time_period=selected_time_period, labels=labels, values=values)

        

