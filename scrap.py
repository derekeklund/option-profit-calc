'''
First, a simple example.

1. Assume we have a process in 3 stages (X1, X2, X3).
2. Each has an average duratin (5, 10, 15 minutes)
3. Each follow a normal distribution and have a variance of 1 minute. The notation of normal distribution is N(average, variance). For example...
    X1 = N(5, 1)
4. We want to know what the probility is that the process will take more than 34 minutes. The total time is...
    Y = X1 + X2 + X3
5. Use numpy
'''

import numpy.random as rnd
import numpy as np

def mc_normal(mean, std_dev, samples):

    results = []
    for _ in range(samples):
        results.append(rnd.normal(mean, std_dev))

    return np.array(results)


# Configuration
s = 100000 # number of samples
upper_limit = 34 # upper limit from specification

# Components
component_1 = mc_normal(5, 1, s)
component_2 = mc_normal(10, 1, s)
component_3 = mc_normal(15, 1, s)

# Relationships
total = component_1 + component_2 + component_3

# Success conditions
probability = np.sum(total > upper_limit)/len(total)*100

print("Probability of exceeding the time limit: ", round(probability, 3), "%")

'''
Now, a more complex example with portfolio returns
https://www.youtube.com/watch?v=6-dhdMDiYWQ
'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
# from pandas_datareader import data as pdr
import yfinance as yf

# Import data
def get_data(stocks, start, end):

    # Get closing data for each stock from Yahoo Finance directly
    for stock in stocks:
        data = yf.download(stock, start=start, end=end)

        # Keep only date and close columns
        data = data[['Close']]
        
        # Change close column name to stock name
        data.columns = [stock]

        if stock == stocks[0]:
            stockData = data

        else:
            stockData = pd.concat([stockData, data[stock]], axis=1)

    # print(stockData)



    # Get daily changes
    returns = stockData.pct_change()

    # print("Returns: ", returns)

    # Calculate mean (daily) returns in a covariance matrix
    meanReturns = returns.mean()

    # print("Mean Returns: ", meanReturns)

    # Covariance means the relationship between two variables (stocks in this case) and to what extent they change together
    # co - together, variance - change
    covMatrix = returns.cov()

    # print("Covariance Matrix: ", covMatrix)

    return meanReturns, covMatrix


stockList = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META']

endDate = dt.datetime.now()
startDate = endDate - dt.timedelta(days=300)

meanReturns, covMatrix = get_data(stockList, startDate, endDate)

print("Mean returns: ", meanReturns)

weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])

print(weights)

# Monte Carlo Method

# Define number of simulations
mc_sims = 100

# Time range in days
T = 100

# 2d array of 100 days with the mean returns repeated for each day
meanMatrix = np.full(shape=(T, len(weights)), fill_value=meanReturns)

# Transpose the matrix
meanMatrix = meanMatrix.T

print("Mean Matrix: ", meanMatrix)

# Portfolio values matrix (100 days x 100 simulations)
portfolio_sims = np.full(shape=(T, mc_sims), fill_value=0.0)

print("Portfolio Sims: ", portfolio_sims)

initialPortfolio = 1000

for m in range(0, mc_sims):
    # MC loops
    # See 11:20 in the video to see how *Multivariate Normal Distribution* is used and how the *Cholesky Decomposition* to determine the *Lower Triangular Matrix* is used for calculations
    # So we get the sample data from the normal distribution and we correlate them with the covariance matrix with the lower triangle


    Z = np.random.normal(size=(T, len(weights)))

    # Lower triangle
    L = np.linalg.cholesky(covMatrix)

    # Note that dot and inner are similar. See docs
    # dailyReturns = meanMatrix + np.dot(L, Z.T)
    dailyReturns = meanMatrix + np.inner(L, Z)

    # Accumulate the daily returns across the days
    portfolio_sims[:, m] = np.cumprod(np.inner(weights, dailyReturns.T) + 1)*initialPortfolio

plt.plot(portfolio_sims)
plt.ylabel('Portfolio Value ($)')
plt.xlabel('Days')
plt.title('Monte Carlo Simulation of a Stock Portfolio')
plt.show()

# Note* the covariance matrix and the time period are extremely important parameters