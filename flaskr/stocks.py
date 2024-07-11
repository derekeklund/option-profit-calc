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

    # Get tickers for the stocks we want to track
    # print("Watchlist: ", watchlist)

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
    # Get last 30 days of prices
    hist = current_company.history(period='1mo')

    labels = hist.index
    values = hist['Close']

    labels = [str(label.date()) for label in labels]
    values = [value for value in values]

    print(labels)
    print(values)

    # List of tuples (date, price)
    # data = [
    #     ("01-01-2024", 10),
    #     ("01-02-2024", 20),
    #     ("01-03-2024", 14),
    #     ("01-04-2024", 15),
    #     ("01-05-2024", 22),
    #     ("01-06-2024", 23),
    #     ("01-07-2024", 28),
    #     ("01-08-2024", 24),
    #     ("01-09-2024", 27),
    #     ("01-10-2024", 30),
    #     ("01-11-2024", 32),
    #     ("01-12-2024", 33),
    #     ("01-13-2024", 32),
    #     ("01-14-2024", 35),
    #     ("01-15-2024", 38),
    #     ("01-16-2024", 40),
    #     ("01-17-2024", 50),
    #     ("01-18-2024", 47),
    #     ("01-19-2024", 55),
    #     ("01-20-2024", 59),
    #     ("01-21-2024", 60),
    #     ("01-22-2024", 53),
    #     ("01-23-2024", 50),
    #     ("01-24-2024", 58),
    #     ("01-25-2024", 66),
    #     ("01-26-2024", 69),
    #     ("01-27-2024", 70),
    #     ("01-28-2024", 80),
    #     ("01-29-2024", 75),
    #     ("01-30-2024", 90),
    #     ("01-31-2024", 100),
    # ]

    # labels = [row[0] for row in data]
    # values = [row[1] for row in data]

    # print("labels: ", labels)
    
    if request.method == 'GET':
        print("GET method")


        return render_template('stocks/watchlist.html', prices_dict=prices_dict, time=time, watchlist=watchlist, company_info=company_info, labels=labels, values=values)
    

    if request.method == 'POST':
        print("POST method")

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
            user_action = 'unknown'
        

        # If the user clicked on a ticker to see the financials
        if user_action == 'summary':
            print("User action is summary")

            # Get the ticker that was clicked on from the form
            summary_ticker = request.form['summary']

            session['summary_ticker'] = summary_ticker

            # Get the company info
            current_company = yf.Ticker(summary_ticker)
            company_info = current_company.info

            return render_template('stocks/watchlist.html', prices_dict=prices_dict, watchlist=watchlist, company_info=company_info)


        # If the user added a ticker to the watchlist
        if user_action == 'add_ticker':
            print("User action is add_ticker")

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

            return render_template('stocks/watchlist.html', prices_dict=prices_dict, added_ticker=added_ticker, watchlist=watchlist, company_info=company_info, labels=labels, values=values)

        # If the user removed a ticker from the watchlist
        elif user_action == 'remove_ticker':
            print("User action is remove_ticker")

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

            return render_template('stocks/watchlist.html', prices_dict=prices_dict,watchlist=watchlist, company_info=company_info, labels=labels, values=values)

        

