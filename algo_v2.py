import os
import pandas as pd
import pandas_ta as ta
from datetime import datetime, time, timedelta
from polygon import RESTClient
import yfinance as yf
import alpaca_trade_api as tradeapi

#import matplotlib.pyplot as plt

#using polygon for market data to get simple moving averages and golden crosses
def goldenCross(ticker, time_frame, key, s_days = 50, l_days = 200):
    #to collect enough data
    start_d = datetime.today() - timedelta(days=365)
    end_d = datetime.today()

    #initialize ma array
    sma = [[], []]

    #use polygon to get market data from start to end date
    with RESTClient(key) as client:
        bars = client.stocks_equities_aggregates(ticker, 1, 'day', start_d.strftime('%Y-%m-%d'), end_d.strftime('%Y-%m-%d'))
        
        try:
            data = bars.results
            prices = []
            for dataset in data:
                prices.append(dataset['c'])
            volume = data[-2]['v']
        except:
            prices = []
            volume = 0

    #reverses array so newer prices occur first
    prices = prices[::-1]
    
    #checks if stock has enough historical data / enough data points
    if len(prices) < l_days+time_frame+1:
        #returns empty arrays to be checked later
        return sma

    #calculates the short simple ma for the time designated in time_frame
    for x in range(time_frame):
        sum = 0
        i = 0
        for y in range(x, s_days + x):
            if i == s_days:
                break
            sum += prices[y]
            i += 1
        sma[0].append(sum/s_days)

    #calculates the long simple ma for the time designated in time_frame
    for x in range(time_frame):
        sum = 0
        i = 0
        for y in range(x, l_days + x):
            if i == l_days:
                break
            sum += prices[y]
            i += 1
        sma[1].append(sum/l_days)

    #check for golden_sma
    golden_sma = sma[0][0] > sma[1][0]
    rcent1 = False
    cross_day = None
    for x in range(time_frame):
        if golden_sma and (sma[0][x] <= sma[1][x]):
            rcent1 = True  
            cross_day = x
            break
    
    if golden_sma and rcent1 and volume >= 75000:
        return [True, cross_day]
    else:
        return [False]

#using pandas_ta for buy confirmations
def buyConfirmation(ticker, cross_day):
    #trend confirmations
    rsi = False
    macd = False
    
    
    #load in data using this method
    df = pd.DataFrame()
    df = df.ta.ticker(ticker)

    #get RSI confirmation
    df['RSI'] = df.ta.rsi(append= True)
    #print(df)
    days = 0
    for val in reversed(df['RSI'].tolist()):
        if val > 50 and days < cross_day:
            rsi = True
            break
        else:
            days += 1
    
    #get MACD confirmation
    macd_df = df.ta.macd(close = df['Close'])
    #print(macd_df)
    days = 0
    check = False
    for val in reversed(macd_df['MACDh_12_26_9'].tolist()):
        if val > 0 and check == False and days <= cross_day:
            check = True
            days += 1
        elif val > 0 and check == True and days <= cross_day+3:
            days += 1
        elif val < 0 and check == False and days <= cross_day+3:
            days += 1
        elif val < 0 and check == True and days <= cross_day+3:
            macd = True
            break
        if days > cross_day+3:
            break
    if rsi and macd:
        return True
    else:
        return False

#using pandas_ta for sell signal and confirmations
def sellSignal(ticker, time_frame):
    #here I want to use stoch and stalling ema as main determinant
    stoch = False
    ema_stall = False

    #confirm with RSI and MACD
    rsi = False
    macd = False

    #load in data using this method
    df = pd.DataFrame()
    df = df.ta.ticker(ticker)

    #get the stoch
    stoch_df = df.ta.stoch(high = df['High'], low = df['Low'], close = df['Close'])
    check = 0
    days = 0
    for val in reversed(stoch_df['STOCHd_14_3_3'].tolist()):
        if val > 80 and days < time_frame:
            stoch = True
        else:
            days =+ 1

    #get the ema and see if it is stagnant or falling
    ema = df.ta.ema(close = df['Close'])
    if (ema[-time_frame] - ema[-1]) > .01:
        ema_stall = True
    
    #confirm with RSI
    df['RSI'] = df.ta.rsi(append= True)
    days = 0
    for val in reversed(df['RSI'].tolist()):
        if val < 50 and days < time_frame:
            rsi = True
            break
        else:
            days += 1

    #confirm with MACD
    macd_df = df.ta.macd(close = df['Close'])
    days = 0
    check = False
    for val in reversed(macd_df['MACDh_12_26_9'].tolist()):
        if val < 0 and days <= int(time_frame/2) and check == False:
            check = True
            days += 1
        elif val > 0 and days <= time_frame and check == True:
            macd = True
            break

    if stoch and ema_stall and (rsi or macd):
        return True
    else:
        return False

#print(buyConfirmation('BATRK', 4))


#PLACE ORDERS
#initialize environment
os.environ['APCA_API_BASE_URL'] = 'https://paper-api.alpaca.markets'

#API Creds
api = tradeapi.REST('PKSZN7WVPIXZ104F8026', 'uSYUqCDmqxyhn2aHBunz88d7I7NeHujiGXXndJza', api_version='v2')
account = api.get_account()

#polygon key
key = 'rf69drQkfvcHKpmG8GtJynwqXSUFus1S'

#list of all NYSE, AMEX, NASDAQ symbols that return a years worth of history
df_symbols = pd.read_csv("polygon-list.csv")
#print(df_symbols)
symbols_l = df_symbols['Symbol'].values.tolist()
#symbols_l = symbols_l[:50]
#print(symbols_l)

#print(symbols_l[3000:])

#get list of stocks with buy signals
buys = []
vol = 0
for symbol in symbols_l:
    sig = goldenCross(symbol, 7, key)
    if sig[0] == True:
        print(symbol)
        if buyConfirmation(symbol, sig[1]) == True:
            buys.append(symbol)
print(buys)



#get list of portfolio stocks
portfolio = api.list_positions()

#sell our positions with sell signals / underneath stop loss
for position in portfolio:
    if sellSignal(position.symbol, 7) == True:
        api.close_position(position.symbol)
        print(position.symbol)
    elif float(position.unrealized_plpc) <= -.10:
        api.close_position(position.symbol)
        print(position.symbol)

#get amount of cash to spend
cash = float(account.buying_power) / 3

#buy the stocks on buy list
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
            if int(shares) != 0 and check == True:
               api.submit_order(t, int(shares), 'buy', 'market', 'day')
