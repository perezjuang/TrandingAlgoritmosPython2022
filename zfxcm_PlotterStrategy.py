
import random
from datetime import datetime
from itertools import count
from turtle import color
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from dbOperations.database import Database
from pyti.simple_moving_average import simple_moving_average as sma
from pyti.relative_strength_index import relative_strength_index as rsi
# This function runs once at the beginning of the strategy to create price/indicator streams
timeframe = 'm1'
symbol = 'EUR/USD'
fast_sma_periods = 10
slow_sma_periods = 30

x_values = []

db = Database()
lplt = plt

lplt.ion()

lplt.show(block=False)

fig = plt.figure()

mng = plt.get_current_fig_manager()
#mng.set_window_title(symbol)

ax1 = fig.add_subplot(4, 1, 1)
ax1.clear()

ax2 = fig.add_subplot(4, 1, 2)
ax2.clear()

ax3 = fig.add_subplot(4, 1, 3)
ax3.clear()

ax4 = fig.add_subplot(4, 1, 4)
ax4.clear()

linePrice, = ax1.plot([], [], label='Precio ' + timeframe + ' ' + symbol)
lineEmaFast, = ax1.plot([], [], label='EMA Fast ' + str(fast_sma_periods), color='green')
lineEmaSlow, = ax1.plot([], [], label='EMA Slow ' + str(slow_sma_periods), color='red')
        # lineEmaSlow2, = ax1.plot([], [], label='EMA Slow 2:  ' + str(slow_sma_periods2), color='red')

lineRegrbidClose, = ax2.plot([], [], label='Regresion Lineal Precio ' + timeframe,
                                               color='silver',
                                               linestyle='--')

lineRegrbidClosePrice, = ax2.plot([], [], label='Precio Cierre ' + timeframe,
                                                    color='green')

linestoK, = ax3.plot([], [], label='k' + timeframe, color='green')
linestoD, = ax3.plot([], [], label='d' + timeframe, color='red')

lineslower_sto, = ax3.plot([], [], color='orange')
linesupper_sto, = ax3.plot([], [], color='orange')

linemacd, = ax4.plot([], [], label='MACD' + timeframe, color='red')
linemacdSignal, = ax4.plot([], [], label='SIGNAL' + timeframe, color='blue')

linesmacd0, = ax4.plot([], [], color='green')
linesmacdup, = ax4.plot([], [], color='gray', linestyle='--')
linesmacdlow, = ax4.plot([], [], color='gray', linestyle='--')

def animate(i):
    data_from_db = db.getData(timeframe='m1')
   
    pricedata = data_from_db

    #for index, row in data.iterrows():
    #    data.loc[index, 'lower_sto'] = 20

    x_values = pricedata['date']
    plt.cla()
    plt.xlabel('Date')
    plt.ylabel('Strategy')

    ######################################
    # PRICE
    ######################################
    #plt.plot(x_values, pricedata['bidclose'],color="black",linestyle='solid', label='Price Close')
    linePrice.set_data(x_values, pricedata['bidclose'])
    

    # Calculate Indicators
    ######################################
    # SMA 
    ######################################

    #plt.plot(x_values, sma(pricedata['bidclose'], 10) ,color="green",linestyle='solid', label='sma10')
    #plt.plot(x_values, sma(pricedata['bidclose'], 30) ,color="red",linestyle='solid', label='sma30')

    ax1.autoscale_view(True, True, True)
    ax1.legend(loc='best', prop={'size': 7})
    ax1.relim()

    ax2.autoscale_view(True, True, True)
    ax2.legend(loc='best', prop={'size': 7})
    ax2.relim()

    ax3.autoscale_view(True, True, True)
    ax3.legend(loc='best', prop={'size': 7})
    ax3.relim()

    ax4.autoscale_view(True, True, True)
    ax4.legend(loc='best', prop={'size': 7})
    ax4.relim()

    lplt.draw()
    lplt.pause(0.4)




    plt.title('Infosys')
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    plt.pause(1)


ani = FuncAnimation(plt.gcf(), animate, 6000)
plt.tight_layout()
plt.show()
