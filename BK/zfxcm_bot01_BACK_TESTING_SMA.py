import fxcmpy
import pandas as pd
import numpy as np
import datetime as dt

from pyti.simple_moving_average import simple_moving_average as sma
con = fxcmpy.fxcmpy(config_file='fxcm.cfg')
# Allows for printing the whole data frame
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

df = con.get_candles('EUR/USD', period='D1', start= dt.datetime(2021, 1, 1), end = dt.datetime(2022, 1, 30))

# Define our pip cost and lot size
pip_cost = 10
lot_size = 10

# Define EMA Fast / Slow parameters
fast = 10
slow = 30

# HMA fast and slow calculation
df['hma_fast'] = sma(df['askclose'], fast)
df['hma_slow'] = sma(df['askclose'], slow)

# Entry signals when HMA(fast) corsses above the HMA(slow). Sell signals when HMA(fast) crossed below the HMA(slow).
df['signal'] = np.where(df['hma_fast'] > df['hma_slow'], 1, 0)
df['position'] = df['signal'].diff()
df.tail()

begin_prices = []
end_prices = []
profits = 0

# get open/close price for each open position
for i, row in df.iterrows():
    if row['position'] == 1:
        begin_prices.append(float(row['askclose']))
    if row['position'] == -1:
        end_prices.append(float(row['askclose']))

# Calculating the profit / loss
for i in range(len(begin_prices)):
    profit = (end_prices[i] - begin_prices[i]) * 100 * pip_cost * lot_size
    profits += profit
    print("The return for trade " + str(i + 1) + " is: " + str(int(profit)))

print("The return for the period is: " + str(int(profits)))

# what happens with the positions while they're open, as well

returns = 0

# Gets the number of pips that the market moved during the day
df['difference (pips)'] = (df['askclose'] - df['askclose']) * 100
# df['p/l'] = df['difference'] * pip_cost * lot_size

# Calculates the daily return while a position is active
# 'Total' column records our running profit / loss for the strategy
for i, row in df.iterrows():
    if row['signal'] == 1:
        returns += (row['difference (pips)'] * pip_cost * lot_size)
        df.loc[i, 'total'] = returns
    else:
        df.loc[i, 'total'] = returns

#################don't actually understand the logic here: why do we calculate everyday p/l??  we are not trading every day.
df.tail()


import matplotlib.pyplot as plt

fig = plt.figure(figsize=(24, 16))
ax1 = fig.add_subplot(111, ylabel='GBP/JPY Price')

# Plotting market prices and moving averages
df['askclose'].plot(ax=ax1, color='r', lw=1.)
df[['hma_fast', 'hma_slow']].plot(ax=ax1, lw=2.)

# Placing purple markers for position entry
ax1.plot(df.loc[df.position == 1.0].index,
         df.hma_fast[df.position == 1.0],
         '^', markersize=10, color='m')

# Placing black markers for position exit
ax1.plot(df.loc[df.position == -1.0].index,
         df.hma_slow[df.position == -1.0],
         'v', markersize=10, color='k')

# Plotting of returns
ax2 = ax1.twinx()
ax2.grid(False)
ax2.set_ylabel('Profits in $')
ax2.plot(df['total'], color='green')

plt.show()