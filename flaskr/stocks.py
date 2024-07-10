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
    print("Watchlist route")

    # Get the user's watchlist
    user_id = g.user['id']
    watchlist = get_watchlist(user_id)

    # Get tickers for the stocks we want to track
    print("Watchlist: ", watchlist)

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
    current_company = yf.Ticker('AMZN')
    company_info = current_company.info

    print("company_info: ", company_info['shortName'])

    company_summary = company_info['longBusinessSummary']


    
    if request.method == 'GET':
        print("GET method")

        print("prices_dict: ", prices_dict)


        return render_template('stocks/watchlist.html', prices_dict=prices_dict, time=time, watchlist=watchlist, company_info=company_info)
    
    if request.method == 'POST':
        print("POST method")

        if request.form['ticker'] != '':
            # Get the ticker that was clicked on from the form
            added_ticker = request.form['ticker']

            # Remove the + sign and whitespace
            # added_ticker = added_ticker.replace("+", "").strip()

            # Make uppercase
            added_ticker = added_ticker.upper()

            print("added_ticker: ", added_ticker)

            # Add the ticker to favorites table in database
            error = None

            db = get_db()

            # Check if the ticker is already in the favorites table
            # Why come this won't work?
            if db.execute(
                'SELECT id FROM favorites WHERE ticker = ? AND user_id = ?', (added_ticker, g.user['id'])
            ).fetchone() is not None:
                print("Yup")
                error = 'Ticker is already in your watchlist.'

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

            return render_template('stocks/watchlist.html', prices_dict=prices_dict, added_ticker=added_ticker, watchlist=watchlist)

        else:
            removed_ticker = request.form['remove-ticker']
            print("removed_ticker: ", removed_ticker)

            db = get_db()
            db.execute(
                'DELETE FROM favorites WHERE ticker = ? AND user_id = ?', (removed_ticker, g.user['id'])
            )
            db.commit()

            watchlist = get_watchlist(user_id)
            prices_dict = get_prices_dict(watchlist)

            return render_template('stocks/watchlist.html', prices_dict=prices_dict,watchlist=watchlist)

        

