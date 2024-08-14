from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
import yfinance as yf
import pandas as pd
from datetime import datetime
from flaskr.db import get_db
from werkzeug.security import check_password_hash


def login_user():
    username = None
    password = None

    try:
        username = request.form['username']
        password = request.form['password']
    except Exception as e:
        print("LOGIN EXCEPTION: ", e)

        return None

    db = get_db()
    error = None
    user = db.execute(
        'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()

    if user is None:
        error = 'Incorrect username.'
    elif not check_password_hash(user['password'], password):
        error = 'Incorrect password.'

    if error is None:
        # Clear the session and set the user_id
        session.clear()
        session['user_id'] = user['id']
        user_id = session.get('user_id')

        if user_id is None:
            g.user = None
        else:
            g.user = get_db().execute(
                'SELECT * FROM user WHERE id = ?', (user_id,)
            ).fetchone()

    return
    


def get_moneyness():
    try:
        moneyness = request.form['moneyness']
    except:
        moneyness = 'near'
        pass

    return moneyness


def get_selected_expiration():
    try:
        selected_exp_date = request.form['expiry']
    except:
        selected_exp_date = None
        pass

    return selected_exp_date


def get_buy_write():
    try:
        buy_write = request.form['buy_write']
    except:
        buy_write = 'buy'
        pass

    return buy_write


# Get the user's stock watchlist
def get_watchlist(user_id):
    db = get_db()
    results = db.execute(
        'SELECT ticker FROM favorites WHERE user_id = ?', (user_id,)
    ).fetchall()
    db.commit()

    watchlist = [row['ticker'] for row in results]

    return watchlist


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
