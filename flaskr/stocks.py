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


# https://ibkrcampus.com/ibkr-quant-news/yfinance-library-a-complete-guide/
# https://www.highcharts.com/docs/index
@bp.route('/watchlist', methods=('GET', 'POST'))
def watchlist():
    print("watchlist")

    tickers = ['SPY', 'QQQ', 'NVDA']

    prices_dict = {}

    for t in tickers:

        # Get SPY stock price
        prices = yf.Ticker(t)

        # Get previous couple day's prices
        historical_prices = prices.history(period="5d", interval="1d")

        # Get latest price, % change, and time (AM/PM format)
        latest_price = historical_prices['Close'].iloc[-1].round(2)
        day_before = historical_prices['Close'].iloc[-2].round(2)

        change = ((latest_price - day_before) * 100 / day_before).round(2)

        time = historical_prices.index[-1].strftime('%I:%M %p')

        # Add price and percent change to nested dictionary
        prices_dict[t] = {}
        prices_dict[t]['price'] = latest_price
        prices_dict[t]['change'] = change

    if request.method == 'GET':
        print("GET method")


        return render_template('stocks/watchlist.html', prices_dict=prices_dict, time=time)
    
    if request.method == 'POST':
        print("POST method")

        # Get the ticker that was clicked on from the form
        added_ticker = request.form['ticker']

        # Remove the + sign and whitespace
        added_ticker = added_ticker.replace("+", "").strip()

        print("added_ticker: ", added_ticker)

        # Add the ticker to user tables favorites column in database


        return render_template('stocks/watchlist.html', prices_dict=prices_dict, time=time, added_ticker=added_ticker)

