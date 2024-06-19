# Implementation of Black-Scholes formula in Python
import numpy as np
from scipy.stats import norm
from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.greeks.analytical import delta, gamma, vega, theta, rho

# Define variables 
r = 0.05 # Interest rate (risk-free 1 year Treasure rate). Changes per day
# C:\Users\Derek\Coding Projects\portfolioApp\mysite\1-year-treasury-rate-yield-chart.csv
S = 440.67 # Underlying price
K = 450 # Strike price
T = 104/365 # Time (days out of 365)
sigma = 0.18 # Implied Volatility (was 0.30)

"""
Example:
July 19th, 2024 option chain
- QQQ
- Call option 450 strike
- 104 days to expiration
- Underlying price 440
- Actual delta = 0.4940

*** Next step would be to pull these from some source. Alpaca maybe? ***

Calculations:
- Actual price of option = 15.42
- Calculated price = 15.50 (<1% off)

- Actual delta = 0.494
- Calculated delta = 0.491 (<1% off)

- Actual theta = -0.1096
- Calculated theta = -0.1087 (<1% off)

- Actual gamma = 0.0096
- Calculated gamma = 0.0094 (~2% off)

- Actual vega = 0.937
- Calculated vega = 0.938 (<1% off)

- Actual rho = 0.5771
- Calculated rho = 0.5727 (<1% off)
"""

def blackScholes(r, S, K, T, sigma, type="c"):
    "Calculate BS price of call/put"
    """
    Black-Scholes requires 5 inputs:
    1. Risk-free rate for 1 year treasury (r)
    2. Underlying Stock price (S)
    3. Strike price (K)
    4. Time to expiration (T)
    5. Implied Volatility (sigma)
    6. Option type (c for call, p for put) 

    C = call option price
    N = normal distribution

    C = (SN * d1) - (Ke ^ rt)(N * d2)

    d1 = [ln(S/K) + (r + 0.5 * sigma^2)t] / (sigma * sqrt(t))
    d2 = d1 - sigma*sqrt(t)

    * remember, ln stands for 'natural logarithm'
    """
    if T == 0:
        T = 0.0001

    d1 = (np.log(S/K) + (r + sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    try:
        if type == "c":
            price = S*norm.cdf(d1, 0, 1) - K*np.exp(-r*T)*norm.cdf(d2, 0, 1)
        elif type == "p":
            price = K*np.exp(-r*T)*norm.cdf(-d2, 0, 1) - S*norm.cdf(-d1, 0, 1)
        return price, bs(type, S, K, T, r, sigma)
    except:
        print("Please confirm option type, either 'c' for Call or 'p' for Put!")

def delta_calc(r, S, K, T, sigma, type="c"):
    "Calculate delta of an option"
    d1 = (np.log(S/K) + (r + sigma**2/2)*T)/(sigma*np.sqrt(T))
    try:
        if type == "c":
            delta_calc = norm.cdf(d1, 0, 1)
        elif type == "p":
            delta_calc = -norm.cdf(-d1, 0, 1)
        return delta_calc, delta(type, S, K, T, r, sigma)
    except:
        print("Please confirm option type, either 'c' for Call or 'p' for Put!")

def theta_calc(r, S, K, T, sigma, type="c"):
    "Calculate BS price of call/put"
    d1 = (np.log(S/K) + (r + sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    try:
        if type == "c":
            theta_calc = -S*norm.pdf(d1, 0, 1)*sigma/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(d2, 0, 1)
        elif type == "p":
            theta_calc = -S*norm.pdf(d1, 0, 1)*sigma/(2*np.sqrt(T)) + r*K*np.exp(-r*T)*norm.cdf(-d2, 0, 1)
        return theta_calc/365, theta(type, S, K, T, r, sigma)
    except:
        print("Please confirm option type, either 'c' for Call or 'p' for Put!")

def gamma_calc(r, S, K, T, sigma, type="c"):
    "Calculate gamma of a option"
    d1 = (np.log(S/K) + (r + sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    try:
        gamma_calc = norm.pdf(d1, 0, 1)/(S*sigma*np.sqrt(T))
        return gamma_calc, gamma(type, S, K, T, r, sigma)
    except:
        print("Please confirm option type, either 'c' for Call or 'p' for Put!")

def vega_calc(r, S, K, T, sigma, type="c"):
    "Calculate BS price of call/put"
    d1 = (np.log(S/K) + (r + sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    try:
        vega_calc = S*norm.pdf(d1, 0, 1)*np.sqrt(T)
        return vega_calc*0.01, vega(type, S, K, T, r, sigma)
    except:
        print("Please confirm option type, either 'c' for Call or 'p' for Put!")

def rho_calc(r, S, K, T, sigma, type="c"):
    "Calculate BS price of call/put"
    d1 = (np.log(S/K) + (r + sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    try:
        if type == "c":
            rho_calc = K*T*np.exp(-r*T)*norm.cdf(d2, 0, 1)
        elif type == "p":
            rho_calc = -K*T*np.exp(-r*T)*norm.cdf(-d2, 0, 1)
        return rho_calc*0.01, rho(type, S, K, T, r, sigma)
    except:
        print("Please confirm option type, either 'c' for Call or 'p' for Put!")
    

# print("Option price: ", blackScholes(r, S, K, T, sigma, "c"))
# print("Delta: ", delta_calc(r, S, K, T, sigma, "c"))
# print("Theta: ", theta_calc(r, S, K, T, sigma, "c"))
# print("Gamma: ", gamma_calc(r, S, K, T, sigma, "c"))
# print("Vega: ", vega_calc(r, S, K, T, sigma, "c"))
# print("Rho: ", rho_calc(r, S, K, T, sigma, "c"))


# For later, you can calulate the standard deviation with np.std()
# https://www.calculator.net/standard-deviation-calculator.html?numberinputs=0.494%2C+0.491&ctype=p&x=Calculate
# np.std([0.494, 0.491]) # 0.0015

# print(np.std([15.42, 15.50])) # 0.04

# Now how to get 1SD, 2SD, 3SD...

print("hi from the greeks.py file!")

"""
def blackScholes(r, S, K, T, sigma, type="c"):
    "Calculate BS price of call/put"
    
    Black-Scholes requires 5 inputs:
    1. Risk-free rate for 1 year treasury (r)
    2. Underlying Stock price (S)
    3. Strike price (K)
    4. Time to expiration (T)
    5. Implied Volatility (sigma)
    6. Option type (c for call, p for put) 
"""

option_price = blackScholes(0.05, 213, 208, 1/365, 0.2, type='c')

print("Option price: ", round(option_price[1], 2))