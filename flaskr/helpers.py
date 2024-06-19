from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
import yfinance as yf
import pandas as pd
from datetime import datetime
from flaskr.db import get_db


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

