import pandas as pd
import sqlite3
from flaskr.db import get_db

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