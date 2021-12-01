import numpy as np
import pandas as pd
import csv
from datetime import datetime, timedelta
from polygon import RESTClient
import yfinance as yf
import matplotlib.pyplot as plt

d2 = datetime.today() - timedelta(days=1)
d1 = d2 - timedelta(days=365)
d3 = d2 - timedelta(days=30)
start_d = d1.strftime('%Y-%m-%d')
end_d = d2.strftime('%Y-%m-%d')
rsi_d = d3.strftime('%Y-%m-%d')

def movingAverages(ticker, time_frame, key, s_sma_days = 50, l_sma_days = 200, s_ema_days = 12, l_ema_days = 26, smoothing = 2):
    #dates for polygon api
    start_d = datetime.today() - timedelta(days=365)
    end_d = datetime.today()

    #array with short and long simple moving average
    sma = [[], []]
    #array with short and long exponential moving average
    ema = [[], []]

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
    if len(prices) < l_sma_days+time_frame+1:
        #returns empty arrays to be checked later
        return [sma, ema]

    #calculates the short simple ma for the time designated in time_frame
    for x in range(time_frame):
        sum = 0
        i = 0
        for y in range(x, s_sma_days + x):
            if i == s_sma_days:
                break
            sum += prices[y]
            i += 1
        sma[0].append(sum/s_sma_days)

    #calculates the long simple ma for the time designated in time_frame
    for x in range(time_frame):
        sum = 0
        i = 0
        for y in range(x, l_sma_days + x):
            if i == l_sma_days:
                break
            sum += prices[y]
            i += 1
        sma[1].append(sum/l_sma_days)

    #sample short sma to be used in ema calculation
    sum = 0
    for x in range(time_frame, time_frame + s_ema_days):
        sum += prices[x]
    samp_s_sma = sum / (s_ema_days)

    #sample long sma to be used in ema calculation
    sum = 0
    for x in range(time_frame, time_frame + l_ema_days):
        sum += prices[x]
    samp_l_sma = sum / (l_ema_days)

    s_factor = (smoothing / (1 + s_ema_days))
    l_factor = (smoothing / (1 + l_ema_days))

    #goes backwards through time_frame, calculating each more recent short term EMA
    for x in reversed(range(0, time_frame)):
        if x == time_frame - 1:
            ema[0].append(prices[x] * s_factor + samp_s_sma * (1 - s_factor))
        else:
            ema[0].append(prices[x] * s_factor + ema[0][-1] * (1 - s_factor))
    #same process for long term EMAs
    for x in reversed(range(0, time_frame)):
        if x == time_frame - 1:
            ema[1].append(prices[x] * l_factor + samp_l_sma * (1 - l_factor))
        else:
            ema[1].append(prices[x] * l_factor + ema[1][-1] * (1 - l_factor))

    #reverses ema lists
    ema[0] = ema[0][::-1]
    ema[1] = ema[1][::-1]

    #plt.figure(1)
    #plt.plot(ema[0])
    #plt.plot(ema[1])

    #plt.show()

    #returns SMA and EMA
    return [sma, ema, volume]
    
def buySignal(ticker, time_frame, key, smoothing=2):
    
    #get simple moving averages and assign each into list for comprehensibility
    ma = movingAverages(ticker, time_frame, key)
    s_sma = ma[0][0]
    l_sma = ma[0][1]

    s_ema = ma[1][0]
    l_ema = ma[1][1]
    
    #makes sure data isnt invalid
    if len(s_sma) == 0:
        return None
    if len(s_ema) == 0:
        return None

    #getting the moving average convergence divergence (macd) line
    macd_line = []
    for x in range(len(s_ema)):
        macd_line.append(s_ema[x] - l_ema[x])

    #prior macd used for last signal line calculation
    samp_macd = macd_line[-1] - (macd_line[-2] - macd_line[-1])
    
    #create signal line as ema of past 9 macds
    sig_line = []
    sig_days = 9
    
    for x in reversed(range(0, time_frame)):
        if x == time_frame - 1:
            sig_line.append(macd_line[x] * (smoothing / (1 + sig_days)) + samp_macd * (1 - (smoothing / (1 + sig_days))))
            
        else:
            sig_line.append(macd_line[x] * (smoothing / (1 + sig_days)) + sig_line[time_frame-2-x] * (1 - (smoothing / (1 + sig_days))))

    #turn macd and signal to displau old --> new on graph
    macd_line = macd_line[::-1]
    
    #plt.figure(1)
    #plt.plot(macd_line, 'r')
    #plt.plot(sig_line, 'b')
    #plt.show()

    #check if macd is increasing
    macd_signal = None
    #see if macd crosses signal within time frame
    for x in range(1, time_frame):
        if macd_line[x-1] - sig_line[x-1] < 0 and macd_line[x] - sig_line[x] > 0:
            macd_signal = True
        elif macd_line[x-1] - sig_line[x-1] > 0 and macd_line[x] - sig_line[x] < 0:
            macd_signal = False

    #check if golden cross happened recently
    golden_sma = s_sma[0] > l_sma[0]
    golden_ema =  s_ema[0] > s_sma[0]

    #checks if these crosses happened recentl
    rcent1 = False
    rcent2 = False
    for x in range(time_frame):
        if golden_sma and (s_sma[x] <= l_sma[x]) and rcent1 == False:
            rcent1 = True  
        elif golden_ema and (s_ema[x] <= l_ema[x]) and rcent2 == False:
            rcent2 = True  

    #if short-term mas are increasing 
    inc_sma = ((s_sma[0] - s_sma[time_frame - 1]) / time_frame) > 0 
    inc_ema = ((s_ema[0] - s_sma[time_frame - 1]) / time_frame) > 0

    #makes sure there is enough volume
    vol = ma[2] > 75000

    #print(golden_sma)
    #print(rcent1)
    #print(golden_ema)
    #print(rcent2)
    #print(inc_sma)
    #print(inc_ema)
    #print(vol)
    #print(macd_signal)

    #plt.figure(2)
    #plt.plot(s_sma, 'r')
    #plt.plot(l_sma, 'b')

    #plt.show()

    if (golden_sma and rcent1) and inc_sma and vol and macd_signal == True: #or (golden_ema and rcent2))
        return 'buy'
    
def sellSignal(ticker, time_frame, key):

    #Stochastic is above 85ish
    #RSI above 70%
    #stop loss under 20%

    #is the ema stalling
    ma = movingAverages(ticker, time_frame, key)
    short_ema = ma[1][0]
    sma = ma[0][0]
    ema_stall = False
    if short_ema[0] < short_ema[-1]:
        ema_stall = True

    #get data for stochastic oscillator
    data = yf.download(tickers = ticker, period= '1mo', interval='30m')
    prices = data['Close'].tolist()
    prices = prices[::-1]

    #calculate fast stochastic oscillator, slow stochastic oscillator
    fast_indexs = []
    days= 0
    for x in range(1, len(prices)-1):
        if days == time_frame*16:
            break
        lastC = prices[x-1]
        low14 = min(prices[x:142+x])
        high14 = max(prices[x:142+x])
        stoch_ind = ((lastC - low14) / (high14 - low14)) * 100
        fast_indexs.append(stoch_ind)
        days+=1

    slow_indexs = []
    for x in range(0, time_frame):
        slow_indexs.append(sum(fast_indexs[x:39+x]) / 39)

    stochastic = False
    for val in slow_indexs:
        if val > 85:
            stochastic = True

    #get RSI
    rsi = True #change to false once finished
    #with RESTClient(key) as client:
    #    bars = client.stocks_equities_aggregates(ticker, 1, 'day', rsi_d.strftime('%Y-%m-%d'), end_d.strftime('%Y-%m-%d'))
    #    try:
    #        data = bars.results
    #        opens = []
    #        closes = []
    #        for dataset in data:
    #            opens.append(dataset['o'])
    #            closes.append(dataset['c'])   
    #    except:
    #        opens = []
    #        closes = []

    #for x in range(opens):


    if ema_stall and stochastic == True and rsi == True:
        return 'sell'

    return None




