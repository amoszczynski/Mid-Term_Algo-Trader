import os
import numpy as np
import pandas as pd
import yfinance as yf
import alpaca_trade_api as tradeapi
from signaling import *

#change for when not using paper account
os.environ['APCA_API_BASE_URL'] = 'https://paper-api.alpaca.markets'

#API Creds
ALPACA_PUBLIC_KEY = #insert public key here
ALPACA_PRIVATE_KEY = #insert private key here
api = tradeapi.REST(ALPACA_PUBLIC_KEY, ALPACA_PRIVATE_KEY, api_version='v2')
account = api.get_account()

#polygon key
key = #polygon.io api key

#list of all NYSE, AMEX, NASDAQ symbols that return a years worth of history
df_symbols = pd.read_csv("polygon-list.csv")
#print(df_symbols)
symbols_l = df_symbols['Symbol'].values.tolist()
#symbols_l = symbols_l[675:700]
#print(symbols_l)

#get list of stocks with buy signals
buys = []
vol = 0
for symbol in symbols_l:
  
    if buySignal(symbol, 7, key) == 'buy':
        print(symbol)
        buys.append(symbol)
print(buys)

#get list of portfolio stocks
portfolio = api.list_positions()


for position in portfolio:
    if sellSignal(position.symbol, 7, key) == 'sell':
        api.close_position(position.symbol)
        print(position.symbol)
    elif float(position.unrealized_plpc) <= -.15:
        api.close_position(position.symbol)
        print(position.symbol)
       

#get amount of cash to spend
cash = float(account.buying_power) / 2

#buy them stocks
if len(buys) != 0:
    buy_pow = cash / len(buys) 
    
    check = False
    if bool(portfolio) == False:
        check = True
    for t in buys:
        for position in portfolio:
            if position.symbol not in buys:
                check = True
        stock = yf.Ticker(t)
        tprice = stock.info['regularMarketPrice']    

        shares = round(buy_pow / tprice, 2)

        try:
            if shares != 0 and check == True:
               api.submit_order(t, shares, 'buy', 'market', 'day')
        except:
            if shares != 0 and check == True:
               api.submit_order(t, int(shares), 'buy', 'market', 'day')

