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

    tickers = ['SPY', 'QQQ', 'NVDA', 'AAPL', 'AMZN', 'MSFT', 'AAPL', 'TSLA', 'META']

    prices_dict = {}

    for t in tickers:

        # Get SPY stock price
        prices = yf.Ticker(t)

        # Get previous day's stock prices
        historical_prices = prices.history(period="1d", interval="15m")

        # Get latest price and time (PM format)
        latest_price = historical_prices['Close'].iloc[-1].round(2)
        time = historical_prices.index[-1].strftime('%I:%M %p')

        # Add ticker & price to dictionary
        prices_dict[t] = latest_price


    return render_template('stocks/watchlist.html', prices_dict=prices_dict, time=time)