import pandas as pd
import sqlite3
from flaskr.db import get_db

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

bp = Blueprint('utils', __name__)

'''
This file is used to update the database with new information.
'''

def get_company_info():
    # Create a connection to the database
    # CSV file to sqlite3 database
    # Currently errors when running utils.py directly.
    # Need to add it to the __init__.py file (app factory)
    db = get_db()

    # Load company-info.csv into dataframe
    df_company_info = pd.read_csv('company-info.csv')

    print(df_company_info)

    counter = 1
    for index, row in df_company_info.iterrows():
        ticker = row['Symbol']
        name = row['Name']
        country = row['Country']
        try:
            ipo_year = int(row['IPO Year'])
        except:
            ipo_year = row['IPO Year']
        sector = row['Sector']
        industry = row['Industry']

        print(f'Ticker: {ticker}, Name: {name}, Country: {country}, IPO Year: {ipo_year}, Sector: {sector}, Industry: {industry}')

        try:
            db.execute(
                'INSERT INTO company_info (ticker, name, country, ipo_year, sector, industry)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (ticker, name, country, ipo_year,sector, industry)
            )
        except Exception as e:
            print(f'{ticker} error:', e)

        db.commit()

        # if counter == 10:
        #     break

        counter += 1

    # return redirect(url_for('blog.index'))


def nasdaq_100_into_db():
    db = get_db()

    # Load csv into dataframe
    df_nasdaq_100 = pd.read_csv('nasdaq_100_stocks.csv')

    print(df_nasdaq_100)

    counter = 1
    for index, row in df_nasdaq_100.iterrows():
        ticker = row['Symbol']

        # Get company_id from company_info table
        company_id = db.execute(
            'SELECT company_id FROM company_info WHERE ticker = ?',
            (ticker,)
        ).fetchone()

        print(f'Company ID: {company_id[0]}')

        try:
            db.execute(
                'INSERT INTO nasdaq_100 (company_id, ticker)'
                ' VALUES (?, ?)',
                (company_id[0], ticker)
            )
        except Exception as e:
            print(f'{ticker} error:', e)

        db.commit()

        # if counter == 10:
        #     break

        counter += 1


def standards_and_poors_into_db():
    db = get_db()

    # Load company-info.csv into dataframe
    df_standards_and_poors = pd.read_csv('s&p_500_stocks.csv')

    print(df_standards_and_poors)

    counter = 1
    for index, row in df_standards_and_poors.iterrows():
        ticker = row['Symbol']

        print(f'Ticker: {ticker}')

        # Get company_id from company_info table
        company_id = db.execute(
            'SELECT company_id FROM company_info WHERE ticker = ?',
            (ticker,)
        ).fetchone()

        try:
            print(f'Company ID: {company_id[0]}')
        except Exception as e:
            print(f'{ticker} likely not in company_info table... here is the error:', e)

        try:
            db.execute(
                'INSERT INTO s_and_p_500 (company_id, ticker)'
                ' VALUES (?, ?)',
                (company_id[0], ticker)
            )
        except Exception as e:
            print(f'{ticker} error:', e)

        db.commit()

        # if counter == 10:
        #     break

        counter += 1


def russell_into_db():
    db = get_db()

    # Load company-info.csv into dataframe
    df_russell = pd.read_csv('russell_2000_stocks.csv')

    print(df_russell)

    counter = 1
    for index, row in df_russell.iterrows():
        ticker = row['Symbol']

        print(f'Ticker: {ticker}')

        # Get company_id from company_info table
        company_id = db.execute(
            'SELECT company_id FROM company_info WHERE ticker = ?',
            (ticker,)
        ).fetchone()

        try:
            print(f'Company ID: {company_id[0]}')
        except Exception as e:
            print(f'{ticker} likely not in company_info table... here is the error:', e)

        try:
            db.execute(
                'INSERT INTO russell_2000 (company_id, ticker)'
                ' VALUES (?, ?)',
                (company_id[0], ticker)
            )
        except Exception as e:
            print(f'{ticker} error:', e)

        db.commit()

        # if counter == 10:
        #     break

        counter += 1




# Go to this route to update the database with whatever function you want
@bp.route('/update-db', methods=('GET', 'POST'))
def update_db():
    print('Updating database...')

    # get_company_info()

    nasdaq_100_into_db()

    # standards_and_poors_into_db()

    # russell_into_db()



    return render_template('utils/update-db.html')

    

