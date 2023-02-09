import fxcmpy
import pandas as pd
import numpy as np
import datetime as dt
from pyti.simple_moving_average import simple_moving_average as sma

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = pd.read_csv('EUR_USD.csv')

pip_cost = 10
lot_size = 10

fast = 10
slow = 30
mediabig = 1000

df['tickqtyLIMIT'] = 350

df['hma_fast'] = sma(df['bidclose'], fast)
df['hma_slow'] = sma(df['bidclose'], slow)
df['hma_slow_big'] = sma(df['bidclose'], mediabig)



df['tickqty_fast'] = sma(df['tickqty'], 5)

df['signal_buy'] = np.where((df['hma_fast'] > df['hma_slow_big']) &  (df['hma_fast'] > df['hma_slow']) & (df['tickqty_fast'] > df['tickqtyLIMIT']), 1, 0)
df['signal_sell'] = np.where((df['hma_fast'] < df['hma_slow_big']) &  (df['hma_fast'] < df['hma_slow']) & (df['tickqty_fast'] > df['tickqtyLIMIT']), 1, 0)

df['position_buy'] = df['signal_buy'].diff()
df['position_sell'] = df['signal_sell'].diff()

df.to_csv("EUR_USD_BACKTESTING.csv")

begin_prices_buy = []
end_prices_buy = []

begin_prices_sell = []
end_prices_sell = []

profits_sell = 0
profits_buy = 0

# get open/close price for each open position
for i, row in df.iterrows():
    if row['position_buy'] == 1:
        begin_prices_buy.append(float(row['bidclose']))
    if row['position_buy'] == -1:
        end_prices_buy.append(float(row['bidclose']))

# get open/close price for each open position
for i, row in df.iterrows():
    if row['position_sell'] == 1:
        begin_prices_sell.append(float(row['bidclose']))
    if row['position_sell'] == -1:
        end_prices_sell.append(float(row['bidclose']))


# Calculating the profit / loss
for i in range(len(begin_prices_buy)):
    profit_buy = (end_prices_buy[i] - begin_prices_buy[i]) * 100 * pip_cost * lot_size
    profits_buy += profit_buy
    print("The return for trade buys" + str(i + 1) + " is: " + str(int(profit_buy)))

print("The return for the period buy is: " + str(int(profits_buy)))


# Calculating the profit / loss
for i in range(len(begin_prices_sell)):
    profit_sell = (end_prices_sell[i] - begin_prices_sell[i]) * 100 * pip_cost * lot_size
    profits_sell += profit_sell
    print("The return for trade sells" + str(i + 1) + " is: " + str(int(profit_sell)))

print("The return for the period is: " + str(int(profits_sell)))



# what happens with the positions while they're open, as well

returns = 0
# Gets the number of pips that the market moved during the day
#df['difference (pips)'] = (df['bidclose'] - df['bidclose']) * 100
# df['p/l'] = df['difference'] * pip_cost * lot_size

# Calculates the daily return while a position is active
# 'Total' column records our running profit / loss for the strategy
#for i, row in df.iterrows():
#    if row['signal'] == 1:
#        returns += (row['difference (pips)'] * pip_cost * lot_size)
#        df.loc[i, 'total'] = returns
#    else:
#        df.loc[i, 'total'] = returns


df.tail()


import matplotlib.pyplot as plt

fig = plt.figure(figsize=(24, 16))
ax1 = fig.add_subplot(111, ylabel='EUR/USD Price')

# Plotting market prices and moving averages
df['bidclose'].plot(ax=ax1, color='g', lw=1.)
df[['hma_fast', 'hma_slow']].plot(ax=ax1, lw=2.)
df['hma_slow_big'].plot(ax=ax1, color='r', lw=1.)

# Placing purple markers for position entry
ax1.plot(df.loc[df.position_buy == 1.0].index,
         df.hma_fast[df.position_buy == 1.0],
         '^', markersize=10, color='m')

# Placing black markers for position exit
ax1.plot(df.loc[df.position_sell == -1.0].index,
         df.hma_slow[df.position_sell == -1.0],
         'v', markersize=10, color='k')

# Plotting of returns
ax2 = ax1.twinx()
ax2.grid(False)
ax2.set_ylabel('Profits in $')

#ax2.plot(df['total'], color='green')

plt.show()