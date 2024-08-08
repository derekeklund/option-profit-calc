from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
import yfinance as yf
import pandas as pd
from datetime import datetime
from flaskr.db import get_db
from werkzeug.security import check_password_hash


def test_login():
    username = None
    password = None

    try:
        username = request.form['username']
        password = request.form['password']
    except Exception as e:
        print("ERROR: ", e)

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

    print(f"loginTest Username: {username}")
    print(f"loginTest Password: {password}")
    print(f"loginTest User: {user}")
    print(f"loginTest Error: {error}")

    if error is None:
        session.clear()
        session['user_id'] = user['id']
        # return redirect(url_for('index'))
        return redirect(url_for('stocks.watchlist'))
    


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


def get_watchlist(user_id):
    db = get_db()
    results = db.execute(
        'SELECT ticker FROM favorites WHERE user_id = ?', (user_id,)
    ).fetchall()
    db.commit()

    watchlist = [row['ticker'] for row in results]

    return watchlist

