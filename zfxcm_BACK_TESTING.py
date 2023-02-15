import fxcmpy
import pandas as pd
import numpy as np
import datetime as dt
from pyti.simple_moving_average import simple_moving_average as sma
from scipy import signal

# from pyti.exponential_moving_average import exponential_moving_average as sma



pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

#con = fxcmpy.fxcmpy(config_file='fxcm.cfg')
# df = con.get_candles('EUR/USD', period='D1', start= dt.datetime(2021, 12, 15), end = dt.datetime(2022, 1, 30))
# df_data = con.get_candles('EUR/USD', period='m5', number=10000)
# saving the dataframe
# df_data.to_csv('EUR_USD.csv')
df = pd.read_csv('EUR_USD.csv')

# Define our pip cost and lot size
pip_cost = 1
lot_size = 10

# Define EMA Fast / Slow parameters
fast = 3
slow = 5
big1slow = 8
big2slow = 12

# HMA fast and slow calculation
df['hma_fast'] = df['bidclose'].ewm(span=fast).mean()
df['hma_slow'] = df['bidclose'].ewm(span=slow).mean()
df['hma_big1slow'] = df['bidclose'].ewm(span=big1slow).mean()
df['hma_big2slow'] = df['bidclose'].ewm(span=big2slow).mean()
df['hma_big3slow'] = df['bidclose'].ewm(span=200).mean()

df['value1'] = 1
# Find local peaks
df['peaks_min'] = df.iloc[signal.argrelextrema(df['bidclose'].values, np.less, order=10)[0]]['value1']
df['peaks_max'] = df.iloc[signal.argrelextrema(df['bidclose'].values, np.greater, order=10)[0]]['value1']

# Volumen trend
df['tickqtyLIMIT'] = 400
df['volumHight'] = np.where( (df['tickqty'] > df['tickqtyLIMIT'] ) , 1, 0)


df['sell'] = np.where( (df['peaks_max'] == 1) 
                     & (df['hma_fast'] > df['hma_slow'])
                     & (df['hma_slow'] > df['hma_big1slow'])
                     & (df['hma_big1slow'] > df['hma_big2slow'])
                     #& (df['hma_big2slow'] > df['hma_big3slow'])
                     & (df['volumHight'] == 1)
                     & (df['hma_fast'] < df['hma_big3slow'])
                     , 1, 0)


#Close Strategy Operation Sell
operationActive = False
for index, row in df.iterrows():
    if df.loc[index, 'sell'] == 1:
        operationActive = True 
    if operationActive == True:
        df.loc[index, 'sell'] = 1
    if df.loc[index, 'peaks_min'] == 1 :
        operationActive = False
       
    

df['buy'] = np.where( (df['peaks_min'] == 1)
                     & (df['hma_fast'] < df['hma_slow'])
                     & (df['hma_slow'] < df['hma_big1slow'])
                     & (df['hma_big1slow'] < df['hma_big2slow'])
                     #& (df['hma_big2slow'] < df['hma_big3slow'])
                     & (df['volumHight'] == 1)
                     & (df['hma_fast'] > df['hma_big3slow'])
                     , 1, 0)



#Close Strategy Operation Sell
operationActive = False
for index, row in df.iterrows():
    if df.loc[index, 'buy'] == 1:
        operationActive = True
    if operationActive == True:
        df.loc[index, 'buy'] = 1
    if df.loc[index, 'peaks_max'] == 1 :
        operationActive = False


df['signal_sell'] = df['sell'].diff()
df['signal_buy'] = df['buy'].diff()

df.to_csv("EUR_USD_BACKTESTING.csv")

begin_prices_buy = []
end_prices_buy = []

begin_prices_sell = []
end_prices_sell = []

profits = 0
########################################################
# Sell
########################################################  
for i, row in df.iterrows():
    if df.loc[i, 'signal_sell'] == 1:
        #BidCloseOperationStart = float(df.loc[i, 'bidclose'])
        begin_prices_sell.append(float(df.loc[i, 'bidclose']))
        index = i
        ActiveStopLoss = False
        BidCloseValueStopLoss = 0
        while index < len(df.index):
            # Stop Loss Calcule
            #if ActiveStopLoss == False:
            #    BidCloseOperationFinish = ((BidCloseOperationStart - float(
            #        df.loc[index, 'bidclose'])) * 1000 * pip_cost * lot_size) - 2

            EndPositionTrade = False
            if df.loc[index, 'signal_sell'] == -1:
                #if ActiveStopLoss == True:
                #    end_prices_sell.append(BidCloseValueStopLoss)
                #else:
                    end_prices_sell.append(float(df.loc[index, 'bidclose']))
                    EndPositionTrade = True

            #if BidCloseOperationFinish <= -10 and EndPositionTrade == False:
            #    df.loc[index, 'sell'] = False
            #    df.loc[index, 'signal_sell'] = 0
            #    if ActiveStopLoss == False:
            #        BidCloseValueStopLoss = float(df.loc[index, 'bidclose'])
            #    ActiveStopLoss = True

            if EndPositionTrade:
                index = len(df.index)

            index += 1
########################################################
# Buy
########################################################  
i = 0
index = 0
for i, row in df.iterrows():
    if df.loc[i, 'signal_buy'] == 1:
        #BidCloseOperationStart = float(df.loc[i, 'bidclose'])
        begin_prices_buy.append(float(df.loc[i, 'bidclose']))
        index = i
        ActiveStopLoss = False
        BidCloseValueStopLoss = 0
        while index < len(df.index):
            # Stop Loss Calcule
            #if ActiveStopLoss == False:
            #    BidCloseOperationFinish = ((BidCloseOperationStart - float(
            #        df.loc[index, 'bidclose'])) * 1000 * pip_cost * lot_size) - 2
            EndPositionTrade = False
            if df.loc[index, 'signal_buy'] == -1:
                #if ActiveStopLoss == True:
                #    end_prices_buy.append(BidCloseValueStopLoss)
                #else:
                    end_prices_buy.append(float(df.loc[index, 'bidclose']))
                    EndPositionTrade = True
            #if BidCloseOperationFinish <= -10 and EndPositionTrade == False:
            #    df.loc[index, 'buy'] = False
            #    df.loc[index, 'signal_buy'] = 0
            #    if ActiveStopLoss == False:
            #        BidCloseValueStopLoss = float(df.loc[index, 'bidclose'])
            #    ActiveStopLoss = True
            if EndPositionTrade:
                index = len(df.index)
            index += 1

begin_prices_sell = begin_prices_sell[:len(end_prices_sell)]
begin_prices_buy = begin_prices_buy[:len(end_prices_buy)]

# Calculating the profit / loss SELL Manually
i = 0
profits = 0
for i in range(len(begin_prices_sell)):
    profit = ( (begin_prices_sell[i] - end_prices_sell[i]) * 1000 * pip_cost * lot_size ) - 5
    profits += profit
    print("The return for trade SELL" + str(i + 1) + " is: " + str(int(profit)))


i = 0
for i in range(len(begin_prices_buy)):
    profit = ((end_prices_buy[i] - begin_prices_buy[i]) * 1000 * pip_cost * lot_size ) - 5
    profits += profit 
    print("The return for trade BUY" + str(i + 1) + " is: " + str(int(profit)))

print("Profit: " + str(profits))

# Calculating the profit position


import matplotlib.pyplot as plt

fig = plt.figure(figsize=(24, 16))
ax1 = fig.add_subplot(111, ylabel='EUR/USD Price')

# Plotting market prices and moving averages
df['bidclose'].plot(ax=ax1, color='b', lw=1.)
df[['hma_fast', 'hma_slow']].plot(ax=ax1, lw=2. )
df[['hma_big1slow', 'hma_big2slow', 'hma_big3slow']].plot(ax=ax1, lw=3.)



# Placing purple markers for position entry

ax1.plot(df.bidclose.index,
         df.bidclose,
         '--', markersize=10, color='blue')

ax1.plot(df.loc[df.signal_sell == 1.0].index,
         df.bidclose[df.signal_sell == 1.0],
         'v', markersize=10, color='red')

ax1.plot(df.loc[df.signal_sell == -1.0].index,
         df.bidclose[df.signal_sell == -1.0],
         '.', markersize=10, color='red')

ax1.plot(df.loc[df.signal_buy == 1.0].index,
         df.bidclose[df.signal_buy == 1.0],
         '^', markersize=10, color='green')

ax1.plot(df.loc[df.signal_buy == -1.0].index,
         df.bidclose[df.signal_buy == -1.0],
         '.', markersize=10, color='green')





ax1.plot(df.loc[df.peaks_max == 1].index,
df.bidclose[df.peaks_max == 1],
'-', markersize=10, color='black')

ax1.plot(df.loc[df.peaks_min == 1].index,
df.bidclose[df.peaks_min == 1],
'-', markersize=10, color='black')


# Plotting of returns
ax2 = ax1.twinx()
ax2.grid(False)
ax2.set_ylabel('Profits in $')
# ax2.plot(df['total'], color='green')

plt.show()
