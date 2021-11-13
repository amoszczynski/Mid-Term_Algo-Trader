# Mid-Term_Algo-Trader
Uses Historical Market data to calculate trend and momentum indicators for all small-cap and larger equtiies in NYSE, NASDAQ, and AMEX, and buy and sell equities accordingly.

Creates short and long simple moving averages and exponential moving averages, as well as the MACD indicator. Uses a combination of these to place buy orders on equities that have upward trends in the short and mid-term. Also calculates stochastic oscillator which is a factor in placing a sell order.

Uses Polygon.io Stocks API, yfinance, and Alpaca Trading API for market data and for placing orders.  

signaling.py --> analyzes data and returns buy/sell signal
algo-trader.py --> calls signaling.py functions and places buy/sell orders
polygon-list.csv --> file containing list of all small-cap and larger equities in NYSE, NASDAQ, and AMEX, used in algo-trader.py

This code is to be automated (I used google cloud platform's cloud functions and cloud scheduler features)
