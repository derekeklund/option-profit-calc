# flask --app flaskr run --debug

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

bp = Blueprint('options', __name__)

import yfinance as yf
import pandas as pd
from datetime import datetime
from flaskr.db import get_db
from .helpers import get_moneyness, get_selected_expiration, get_buy_write, login_user, get_watchlist, get_prices_dict


@bp.route('/scanner', methods=('GET', 'POST'))
def scanner():
    print("In scanner route")

    show_div = False

    # If user submits a ticker, redirect to the same page
    if request.method == 'POST':

        # Check if user has entered login info in from this page
        username = None

        try:
            username = request.form['username']
        except:
            pass

        # If yes, log user in + refresh page
        if username != None:
            login_user()

            return render_template('options/scanner.html', show_div=show_div)

        moneyness = get_moneyness()
        print("Moneyness:", moneyness)

        selected_exp_date = get_selected_expiration()
        print("Expiry date:", selected_exp_date)

        # Show 'calls' and 'puts' text in the table
        show_div = True

        ticker = request.form['symbol'].upper()
        print("Ticker:", ticker)
        error = None

        ticker = yf.Ticker(ticker)
        exp_dates = ticker.options

        try:
            if selected_exp_date == None:
                options_chain = ticker.option_chain(date=exp_dates[0])
            else:
                options_chain = ticker.option_chain(date=selected_exp_date)
        except:
            error = 'No options data available for this ticker.'
            flash(error)
            return render_template('options/scanner.html')

        # Get calls and puts and trim to only the columns we want
        calls = options_chain.calls[['lastPrice', 'change', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility', 'strike']]
        puts = options_chain.puts[['lastPrice', 'change', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility', 'strike']]

        # All floats to 2 decimal places
        pd.options.display.float_format = "{:,.2f}".format

        # Format volume and open interest with no decimals
        calls['volume'] = calls['volume'].apply(lambda x: "{:,.0f}".format(x))
        calls['openInterest'] = calls['openInterest'].apply(lambda x: "{:,.0f}".format(x))
        puts['volume'] = puts['volume'].apply(lambda x: "{:,.0f}".format(x))
        puts['openInterest'] = puts['openInterest'].apply(lambda x: "{:,.0f}".format(x))

        # Merge calls and puts on strike price
        all_options = pd.merge(calls, puts, on='strike', how='outer')

        if selected_exp_date == None:
            all_options['Exp. Date'] = exp_dates[0]
        else:
            all_options['Exp. Date'] = selected_exp_date

        # Reorder columns
        all_options = all_options[['Exp. Date', 'lastPrice_x', 'change_x', 'bid_x', 'ask_x', 'volume_x', 'openInterest_x', 'impliedVolatility_x', 'strike','lastPrice_y', 'change_y', 'bid_y', 'ask_y', 'volume_y', 'openInterest_y', 'impliedVolatility_y']]

        # Rename columns
        col_names = ['Exp. Date', 'Last Price', 'Change', 'Bid', 'Ask', 'Volume', 'Open Interest', 'Implied Volatility', 'Strike', 'Last Price', 'Change', 'Bid', 'Ask', 'Volume', 'Open Interest', 'Implied Volatility']
        all_options.columns = col_names

        # Get previous close of stock
        ticker_info = ticker.info
        previous_close = ticker_info['previousClose']

        # Find the strike price closest to the current price
        closest_strike = all_options['Strike'].sub(previous_close).abs().idxmin()

        if all_options['Strike'][closest_strike] > previous_close:
            insert_ind = closest_strike - 0.5
        else:
            insert_ind = closest_strike + 0.5

        # Insert previous close of stock into the table
        all_options.loc[insert_ind] = ['--', '--', '--', '--', '--', '--', '--', '--', previous_close, '--', '--', '--', '--', '--', '--', '--']
        all_options = all_options.sort_index().reset_index(drop=True)

        # Get index of previous close
        ind_previous_close = all_options[all_options['Strike'] == previous_close].index[0]

        if moneyness == 'near':
            # Trim to only 20 strikes that are near-the-money
            all_options = all_options.iloc[ind_previous_close - 10:ind_previous_close + 11]

        # Pandas to html 
        all_options_table = all_options.to_html(header=True, na_rep="--", classes='pd-table scanner', index=False, formatters={'Strike': lambda x: f'<b>{x}</b>'},escape=False)

        print("selected_exp_date:", selected_exp_date)
        print("expiries:", exp_dates)
        print("show_div:", show_div)


        return render_template('options/scanner.html', tables=[all_options_table], show_div=show_div, expiries=exp_dates, selected_exp_date=selected_exp_date, moneyness=moneyness)
    
    else:
        return render_template('options/scanner.html', show_div=show_div)
    

@bp.route('/profit-calc', methods=('GET', 'POST'))
def profit_calc():
    
    show_div = False
    
    if request.method == 'GET':
        # session.clear() # Removed bc it was logging user out

        moneyness = get_moneyness()
        
        print("GET request.")

        return render_template('options/profit-calc.html', show_div=show_div)


    if request.method == 'POST':
        print("POST request")

        # Check if user has entered login info in from this page
        username = None

        try:
            username = request.form['username']
        except:
            pass

        # If yes, log user in + refresh page
        if username != None:
            login_user()

            return render_template('options/profit-calc.html', show_div=show_div)

        tables = []

        profit_loss_table = session.get('profit_loss_table')

        strike = None
        show_div = True

        moneyness = get_moneyness()
        print("Moneyness:", moneyness)

        buy_write = get_buy_write()
        print("Buy write:", buy_write)

        try:
            json_values = request.get_json()

        except:
            json_values = None
            pass

        
        if json_values != None:
            symbol = json_values['symbol']
            strike = json_values['strike']
            expiry = json_values['expiry']
            upper_bound = int(json_values['upper_bound'])
            lower_bound = int(json_values['lower_bound'])
            price = float(json_values['price'])
            buy_write = json_values['buy_write']

            print("initial Json strike:", strike)

            # Split the string to get the strike price
            strike_string = strike.split('_')
            option_type = strike_string[0]
            strike = float(strike_string[1])
            initial_strike_value = float(strike_string[2])

            print("-----JSON values-----")
            print("Symbol (symbol):", symbol)
            print("Strike (strike):", strike)
            print("Initial Strike Value (initial_strike_value):", initial_strike_value)
            print("Option type (option_type):", option_type)
            print("Expiry (expiry):", expiry)
            print("Price (price):", price)
            print("Lower bound (lower_bound):", lower_bound)
            print("Upper bound (upper_bound):", upper_bound)
            print("Buy write (buy_write):", buy_write)
            print("---------------------")

            # Get current date
            current_date = datetime.today().strftime('%Y-%m-%d')

            # Get number of days from current date to expiry date
            expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
            current_date = datetime.strptime(current_date, '%Y-%m-%d')
            days_to_expiry = (expiry_date - current_date).days

            # Get range of expiry days
            expiry_range = range(1, days_to_expiry + 1, 1)

            # Creat list of days to expiry
            days_to_expiry_list = list(expiry_range)
            days_to_expiry_list = list(reversed(days_to_expiry_list))
            days_to_expiry_list.append(0)

            # print("********\n days_to_expiry :", days_to_expiry)

            price_range = upper_bound - lower_bound

            # print("Price range:", price_range)

            # If dataframe gets too big, calculate a slice factor to limit the number of table cells to ~400
            if days_to_expiry * price_range > 400:
                slice_factor = round(days_to_expiry / 20)

                # print("Slice factor:", slice_factor)

                # If user selects a wide price range, increase the slice factor
                '''Next step: do the slicing on the rows instead of the columns to keep the number of columns constant'''
                if price_range > 20:
                    range_factor = round(price_range / 10)

                    # print("Range factor:", range_factor)

                    slice_factor = slice_factor * range_factor

                    # print("New slice factor:", slice_factor)

                days_to_expiry_list = days_to_expiry_list[::slice_factor]

                

            # if days_to_expiry_list doesn't have 0, add it
            if 0 not in days_to_expiry_list:
                days_to_expiry_list.append(0)

            # Make dataframe with possible profit/loss scenarios
            expiration_price_range = range(lower_bound, upper_bound, 1)
            expiration_price_list = list(expiration_price_range)
            possible_price_list = list(reversed(expiration_price_list))

            column_header = "Potential Price"

            data = {f'{column_header}': possible_price_list}
            df_profit_loss = pd.DataFrame(data)

            from .greeks import blackScholes

            if option_type == 'call':
                scholes_type = 'c'
            else:
                scholes_type = 'p'

            print("***********************")
            print("Scholes type:", scholes_type)
            print("strike:", strike)
            print("***********************")

            for d in days_to_expiry_list:

                # Calculate option price for each day to expiry at each strike price
                df_profit_loss[f'{d}'] = df_profit_loss[f'{column_header}'].apply(lambda x: round(blackScholes(0.05, x, strike, d/365, 0.2, type=scholes_type)[1], 2)) # x = S (underlying stock price)

            # print("Profit loss table:", df_profit_loss)

            upper_header = "Days to Expiry"
            lower_header = df_profit_loss.columns
            num_columns = len(df_profit_loss.columns)

            df_profit_loss.columns = pd.MultiIndex.from_product([[upper_header], df_profit_loss.columns])

            # print("profit loss table columns:", df_profit_loss.columns)

            # print("Profit loss table:", df_profit_loss)

            def calculate_profit(option_value, initial_strike_value):
                # print("Buy/Write:", buy_write)

                profit = round(option_value - initial_strike_value, 2)

                if buy_write == 'write':
                    profit = profit * -1

                percent = round((profit / initial_strike_value * 100), 0)

                percent = int(percent) 

                # print(f"Profit (percent): {profit} ({percent})")

                return profit, percent
            
            def style_td(percent):

                background = "p0"

                # FYI for below: p100 would be positive 100% profit and p-100 would a 100% loss

                if percent >= 100:
                    background = 'p100'
                elif percent >= 75 and percent < 100:
                    background = 'p75'
                elif percent >= 50 and percent < 75:
                    background = 'p50'
                elif percent >= 25 and percent < 50:
                    background = 'p25'
                elif percent >= 5 and percent < 25:
                    background = 'p5'
                elif percent >= -5 and percent < 5:
                    background = 'p0'
                elif percent >= -25 and percent < -5:
                    background = 'p-5'
                elif percent >= -25 and percent < 0:
                    background = 'p-25'
                elif percent >= -50 and percent < -25:
                    background = 'p-50'
                elif percent >= -75 and percent < -50:
                    background = 'p-75'
                elif percent >= -100 and percent < -75:
                    background = 'p-100'
                elif percent < -100:
                    background = 'p-101'

                return background
            
            if buy_write == 'buy':
                long_short = 'Long'
            else:
                long_short = 'Short'

            if option_type == 'call':
                header_type = 'Call'
            else:
                header_type = 'Put'

            # Add strike to top of table
            # html_pl = f"<p>Selected Strike: <b>{strike}</b></p>"
            html_pl = f"<p><b>{long_short} {strike} {header_type}</b></p>"

            html_pl += f'<table border="1" class="dataframe pd-table profit-table"><thead><tr><th class="top-left-cell"></th><th class="top-right-cell" colspan={num_columns} haligh="left">{upper_header}</th></tr><tr style="text-align: right;">'
            html_pl += '<th>' + '</th><th>'.join(lower_header) + '</th></tr></thead><tbody>'

            # print(df_profit_loss)

            for i, row in df_profit_loss.iterrows():
                html_pl += "<tr>"

                j = 0
                # Iterate over each column value in the row
                for value in row:

                    # print(f"Value: {value}, initial_strike_value: {initial_strike_value}")

                    profit_and_percent = calculate_profit(value, initial_strike_value)

                    profit = profit_and_percent[0]
                    percent = profit_and_percent[1]

                    style = style_td(percent)

                    if j == 0:
                        html_pl += f'<td><b>{value}</b></td>'
                    else:
                        # html_pl += f'<td class="pl-td {style}">{profit} ({value})<span class="highlight-cell">{percent}%</span></td>'
                        html_pl += f'<td class="pl-td {style}">{percent}%<span class="highlight-cell">{value}</span></td>'

                    j += 1

                html_pl += "</tr>"
            html_pl += "</table>"

            # print("HTML PL:", html_pl)

            # Pandas to html
            profit_loss_table = df_profit_loss.to_html(header=True, na_rep="--", classes='pd-table', index=False, formatters={f'{column_header}': lambda x: f'<b>{x}</b>'}, escape=False)

            profit_loss_table = f"<p>Selected Strike: <b>{strike}</b></p>" + profit_loss_table

            # print("Profit loss table:", profit_loss_table)

            # Store table in session
            session['profit_loss_table'] = profit_loss_table # styled_table

            # Styled one
            session['profit_loss_table'] = html_pl

        
        else:

            try:
                expiry = request.form['expiry']
            except:
                expiry = None
                pass

            try:    
                symbol = request.form['symbol'].upper()
            except:
                symbol = None
                pass

            try:
                price = float(request.form['price'])
                
            except:
                price = None
                pass

            print("ELSE symbol:", symbol)
            print("ELSE strike:", strike)
            print("ELSE price:", price)

        error = None

        # Get call options chain
        ticker_obj = yf.Ticker(symbol)

        exp_dates = ticker_obj.options

        try:
            if expiry == None:
                expiry = exp_dates[0]

            options_chain = ticker_obj.option_chain(date=expiry)
        except:
            error = 'No options data available for this ticker.'
            flash(error)
            return render_template('options/profit-calc.html')
        
        # Get calls and puts and trim to only the columns we want
        # MAYBE change this to 'bid' and 'ask' if you can get 15 min delayed data
        # but for now it looks like the 'bid' and 'ask' are all zeroes
        calls = options_chain.calls[['lastPrice', 'strike']]
        puts = options_chain.puts[['lastPrice', 'strike']]

        all_options = pd.merge(calls, puts, on='strike', how='outer')
        all_options.columns = ['Call', 'Strike', 'Put']

        # Get latest price (shouldn't be the previous closing price if the market is open)
        data = ticker_obj.history(period='1d')

        # get last price with ser.iloc
        price = data['Close'].iloc[-1]

        # last_price = data['Close'][0]
        price = round(price, 2)

        lower_bound = int(round(price)) - 10
        upper_bound = int(round(price)) + 10

        # Find the strike price closest to the current price
        closest_strike = all_options['Strike'].sub(price).abs().idxmin()

        if all_options['Strike'][closest_strike] > price:
            insert_ind = closest_strike - 0.5
        else:
            insert_ind = closest_strike + 0.5

        # Insert previous close of stock into the table
        all_options.loc[insert_ind] = ['--', price, '--']
        all_options = all_options.sort_index().reset_index(drop=True)

        # Change all columns to numeric
        all_options = all_options.apply(pd.to_numeric, errors='coerce')

        # Get index of previous close
        ind_previous_close = all_options[all_options['Strike'] == price].index[0]

        if moneyness == 'near':
            # Trim to only 20 strikes that are near-the-money
            all_options = all_options.iloc[ind_previous_close - 10:ind_previous_close + 11]

        # Replace all NaN values with '--'
        all_options = all_options.fillna('--')

        # Create options chain table through iteration
        html = '<table border="1" class="dataframe pd-table"><thead><tr style="text-align: right;">'
        html += '<th>' + '</th><th>'.join(all_options.columns) + '</th></tr></thead><tbody>'

        for i, row in all_options.iterrows():
            html += "<tr>"

            j = 0
            # Iterate over each column value in the row
            for value in row:

                j += 1

                if j == 1:
                    identifier = "call"
                elif j == 2:
                    identifier = "strike"
                elif j == 3:
                    identifier = "put"

                next_strike = all_options["Strike"][i]

                if identifier != "strike":
                    # HTMX link to refresh the table (was 1.2s on 30Aug)
                    html += f'<td><a class="strike-select" href=".top" onclick="getUserInput(this)" hx-target="#profit-loss-table" hx-trigger="click delay:1.5s" hx-swap="innerHTML show:#top-scroll:top" hx-get="/refresh-calc" value="{identifier}_{next_strike}_{value}">{value}</a></td>'

                else:
                    html += f'<td><b>{value}</b></td>'

            html += "</tr>"

        # Close the table tag
        html += "</table>"

        # Append to tables list
        tables.append(html)

        # Add strike to session
        session['strike'] = strike

        print("-----Variable values-----")
        print("Symbol (symbol):", symbol)
        print("Strike (strike):", strike)
        print("Expiry (expiry):", expiry)
        print("Moneyness (moneyness):", moneyness)
        print("Buy write (buy_write):", buy_write)
        print("Price (price):", price)
        print("Lower bound (lower_bound):", lower_bound)
        print("Upper bound (upper_bound):", upper_bound)
        print("---------------------")

        return render_template('options/profit-calc.html', tables=tables, show_div=show_div, last_price=price, selected_strike=strike, expiries=exp_dates, selected_exp_date=expiry, moneyness=moneyness, buy_write=buy_write, lower_bound=lower_bound, upper_bound=upper_bound)


# This refreshes the profit loss table in the profit-calc route
@bp.route('/refresh-calc', methods=('POST', 'GET'))
def refresh_calc():

    print("*****Refresh calc function*****")

    table = session.get('profit_loss_table')
    # print("refreshed table: ", table)

    strike = str(session.get('strike'))
    print("Refreshed strike:", strike)

    if table != None:
        print("Table found in session")
        return table
    else:
        print("\nERROR: No table found in session")

        # Can't refresh b/c gets stuck in a loop
        # refresh_calc()

        return("\nNo table found in session. Please retry!")
    

@bp.route('/max-pain', methods=('GET', 'POST'))
def max_pain():
    print("In Max Pain route")

    expiry = None
    ticker = 'SPY'

    if request.method == 'POST':
        print("POST request")

        # Check if user has entered login info in from this page
        username = None

        try:
            username = request.form['username']
        except:
            pass

        # If yes, log user in + refresh page
        if username != None:
            login_user()

        else:
            # Get ticker + expiration date from form
            expiry = request.form['expiry']
            ticker = request.form['symbol'].upper()

        # Get the form keys
        form_keys = request.form.keys()
        form_keys = list(form_keys)
        print("Form keys:", form_keys)
        

    # Get ticker info
    ticker_obj = yf.Ticker(ticker)

    # Get expiration dates for options
    exp_dates = ticker_obj.options

    # Flash error if no options data is available for ticker
    try:
        if expiry == None or expiry not in exp_dates:
            expiry = exp_dates[0]

        options_chain = ticker_obj.option_chain(date=expiry)
        
    except:
        error = 'No options data available for this ticker.'
        flash(error)

        # On error, get the most recent ticker from session
        ticker = session.get('ticker')

        # Get SPY ticker info
        ticker_obj = yf.Ticker(ticker)

        # Get expiration dates for options
        exp_dates = ticker_obj.options

        options_chain = ticker_obj.option_chain(date=expiry)


    # Get previous close of stock
    ticker_info = ticker_obj.info
    previous_close = ticker_info['previousClose']
 
    # Get calls and puts and trim to only the columns we want   
    calls = options_chain.calls[['strike', 'openInterest']]
    puts = options_chain.puts[['strike', 'openInterest']]

    # Rename columns
    calls.columns = ['strike', 'calls_open_interest']
    puts.columns = ['strike', 'puts_open_interest']

    # Merge calls and puts on strike price
    all_options = pd.merge(calls, puts, on='strike', how='outer')

    # Replace NaN values with 0
    all_options = all_options.fillna(0)

    # New column 'total_open_interest' is the sum of calls and puts open interest
    all_options['total_open_interest'] = all_options['calls_open_interest'] + all_options['puts_open_interest']

    # print("All options:", all_options)

    # Calculate potential losses at each strike
    call_lossess = []
    put_lossess = []
    losses = []

    for i, strike in all_options.iterrows():

        # Get difference between strike price and potential closing price (row['strike'])
        call_loss = sum((max(0, strike['strike'] - row['strike']) * row['calls_open_interest']) for _, row in all_options.iterrows())
        put_loss = sum((max(0, row['strike'] - strike['strike']) * row['puts_open_interest']) for _, row in all_options.iterrows())



        call_lossess.append(call_loss)
        put_lossess.append(put_loss)
        total_loss = call_loss + put_loss
        losses.append(total_loss)

    
    all_options['call_losses'] = call_lossess
    all_options['put_losses'] = put_lossess
    all_options['total_loss'] = losses

    max_pain_strike = all_options.loc[all_options['total_loss'].idxmin(), 'strike']

    # If strike is a whole number, convert to int
    if max_pain_strike % 1 == 0:
        max_pain_strike = int(max_pain_strike)

    # Add new column to dataframe called 'colors' to highlight max pain strike
    all_options['colors'] = ['rgb(255, 99, 132, 0.5)' if strike == max_pain_strike else 'rgba(54, 162, 235, 0.5)' for strike in all_options['strike']]

    # print("All options:", all_options)

    strikes = all_options['strike'].tolist()
    call_losses = all_options['call_losses'].tolist()
    put_losses = all_options['put_losses'].tolist()
    losses = all_options['total_loss'].tolist()
    background_colors = all_options['colors'].tolist()

    session['ticker'] = ticker


    return render_template('options/max-pain.html', labels=strikes, values=losses, max_pain_strike=max_pain_strike, expiries=exp_dates, selected_exp_date=expiry, ticker=ticker, background_colors=background_colors, call_losses=call_losses, put_losses=put_losses, previous_close=previous_close)