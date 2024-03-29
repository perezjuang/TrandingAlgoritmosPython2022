import fxcmpy
import pandas as pd
import numpy as np
import datetime as dt
from pyti.simple_moving_average import simple_moving_average as sma

# from pyti.exponential_moving_average import exponential_moving_average as sma

con = fxcmpy.fxcmpy(config_file='fxcm.cfg')
# Allows for printing the whole data frame
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# df = con.get_candles('EUR/USD', period='D1', start= dt.datetime(2021, 12, 15), end = dt.datetime(2022, 1, 30))
# df_data = con.get_candles('EUR/USD', period='m5', number=10000)
# saving the dataframe
# df_data.to_csv('EUR_USD.csv')
df = pd.read_csv('EUR_USD.csv')

# Define our pip cost and lot size
pip_cost = 1
lot_size = 10

# Define EMA Fast / Slow parameters
fast = 10
slow = 30

# HMA fast and slow calculation
df['hma_fast'] = sma(df['bidclose'], fast)
df['hma_slow'] = sma(df['bidclose'], slow)

df['sell'] = (df['hma_fast'] < df['hma_slow'])
df['buy'] = (df['hma_fast'] > df['hma_slow'])
df['signal'] = np.where(df['hma_fast'] < df['hma_slow'], 1, 0)
df['position_operation'] = df['signal'].diff()

begin_prices_buy = []
end_prices_buy = []

begin_prices_sell = []
end_prices_sell = []

profits = 0

# get open/close price for each open position for sells
for i, row in df.iterrows():
    if df.loc[i, 'position_operation'] == 1 and df.loc[i, 'sell'] == True and df.loc[i, 'signal'] == 1:
        BidCloseOperationStart = float(df.loc[i, 'bidclose'])
        begin_prices_sell.append(float(df.loc[i, 'bidclose']))
        index = i
        ActiveStopLoss = False
        BidCloseValueStopLoss = 0
        while index < len(df.index):
            # Stop Loss Calcule
            if ActiveStopLoss == False:
                BidCloseOperationFinish = ((BidCloseOperationStart - float(
                    df.loc[index, 'bidclose'])) * 1000 * pip_cost * lot_size) - 2

            EndPositionTrade = False
            if df.loc[index, 'position_operation'] == -1 and df.loc[index, 'sell'] == False:
                if ActiveStopLoss == True:
                    end_prices_sell.append(BidCloseValueStopLoss)
                else:
                    end_prices_sell.append(float(df.loc[index, 'bidclose']))
                EndPositionTrade = True

            if BidCloseOperationFinish <= -10 and EndPositionTrade == False:
                df.loc[index, 'position_operation'] = 0
                df.loc[index, 'sell'] = False
                df.loc[index, 'signal'] = 0
                if ActiveStopLoss == False:
                    BidCloseValueStopLoss = float(df.loc[index, 'bidclose'])
                ActiveStopLoss = True

            if EndPositionTrade:
                index = len(df.index)

            index += 1

# get open/close price for each open position for sells
i = 0
for i, row in df.iterrows():
    if df.loc[i, 'position_operation'] == -1 and df.loc[i, 'buy'] == True and df.loc[i, 'signal'] == 0:
        begin_prices_buy.append(float(df.loc[i, 'bidclose']))
        index = i
        while index < len(df.index):
            if df.loc[index, 'position_operation'] == 1 and df.loc[index, 'buy'] == False:
                end_prices_buy.append(float(df.loc[index, 'bidclose']))
                index = len(df.index)
            index += 1

begin_prices_sell = begin_prices_sell[:len(end_prices_sell)]
begin_prices_buy = begin_prices_buy[:len(end_prices_buy)]

# Calculating the profit / loss SELL Manually
i = 0
for i in range(len(begin_prices_sell)):
    profit = (begin_prices_sell[i] - end_prices_sell[i]) * 1000 * pip_cost * lot_size
    profit = profit - 2
    profits += profit
    print("The return for trade SELL" + str(i + 1) + " is: " + str(int(profit)))

i = 0
for i in range(len(begin_prices_buy)):
    profit = (end_prices_buy[i] - begin_prices_buy[i]) * 1000 * pip_cost * lot_size
    profits += profit
    profit = profit - 2
    print("The return for trade BUY" + str(i + 1) + " is: " + str(int(profit)))

print("Profit: " + str(profits))

# Calculating the profit position


import matplotlib.pyplot as plt

fig = plt.figure(figsize=(24, 16))
ax1 = fig.add_subplot(111, ylabel='EUR/USD Price')

# Plotting market prices and moving averages
df['bidclose'].plot(ax=ax1, color='r', lw=1.)
df[['hma_fast', 'hma_slow']].plot(ax=ax1, lw=2.)

# Placing purple markers for position entry
ax1.plot(df.loc[df.position_operation == 1.0].index,
         df.hma_fast[df.position_operation == 1.0],
         'v', markersize=10, color='red')

# Placing black markers for position exit
ax1.plot(df.loc[df.position_operation == -1.0].index,
         df.hma_slow[df.position_operation == -1.0],
         '^', markersize=10, color='green')

# Plotting of returns
ax2 = ax1.twinx()
ax2.grid(False)
ax2.set_ylabel('Profits in $')
# ax2.plot(df['total'], color='green')

plt.show()
