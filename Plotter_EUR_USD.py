import os
from traceback import print_list
from webbrowser import get

from ast import If
import pandas as pd
import matplotlib.pyplot as plt
from dbOperations.database import Database
from pyti.simple_moving_average import simple_moving_average as sma
from pyti.relative_strength_index import relative_strength_index as rsi
from pyti.stochastic import percent_d as sto_percent_d
from pyti.stochastic import percent_k as sto_percent_k

import numpy as np
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.animation as animation
import configparser


config = configparser.ConfigParser()
config.read('RobotV5.ini')


# This function runs once at the beginning of the strategy to create price/indicator streams
time_frame_operations = config['timeframe']
timeframe = time_frame_operations['timeframe']

#symbol = time_frame_operations['symbol']
fileName = str(os.path.basename(__file__))
fileName = fileName.replace(".py", "")
fileName = fileName.replace("Plotter_", "")
symbol = fileName#.replace("_", "/")

numberofcandlesinview = time_frame_operations['numberofcandlesinview']
fast_sma_periods = time_frame_operations['fast_sma_periods']
slow_sma_periods = time_frame_operations['slow_sma_periods']
min = 0
amount_value = 1
vallimit = 4
valstop = -3

db = Database()
plt.style.use('dark_background')

def readData():
    return pd.read_csv(symbol + '.csv') 

class SubplotAnimation(animation.TimedAnimation):        
    def __init__(self):
        fig = plt.figure()
        self.axBase = fig.add_subplot(3, 1, 1)
        self.RSI = fig.add_subplot(3, 1, 2)
        self.VOLUM = fig.add_subplot(3, 1, 3)

        self.t = np.linspace(0, 80, 400)

        self.axBase.set_xlabel('Date')
        self.axBase.set_ylabel('Price Move' + symbol )
        self.linePrice = Line2D([], [], color='white')

        self.lineSMA200 = Line2D([], [], color='green')
        self.lineSMA400 = Line2D([], [], color='red')
        self.ema_res1 = Line2D([], [], color='orange')
        self.ema_res2 = Line2D([], [], color='white')
        self.ema_res3 = Line2D([], [], color='white')
        
        self.axBase.add_line(self.linePrice)
        self.axBase.add_line(self.lineSMA200)
        self.axBase.add_line(self.lineSMA400)
        self.axBase.add_line(self.ema_res1)
        self.axBase.add_line(self.ema_res2)
        self.axBase.add_line(self.ema_res3)

        self.VOLUM.set_xlabel('VOLUM')
        self.VOLUM.set_ylabel('Volumen')
        self.VOLUMLineVolum = Line2D([], [], color='white')
        self.VOLUMLinePromedio = Line2D([], [], color='orange')
        self.VOLUMFast = Line2D([], [], color='green')
        self.VOLUMLimit = Line2D([], [], color='red')

       
        self.VOLUM.add_line(self.VOLUMLineVolum)
        self.VOLUM.add_line(self.VOLUMLinePromedio)
        self.VOLUM.add_line(self.VOLUMFast)
        self.VOLUM.add_line(self.VOLUMLimit)

        self.RSI.set_xlabel('DATE')
        self.RSI.set_ylabel('RSI')
        self.lineRSI_INF = Line2D([], [], color='red')
        self.lineRSI_SUP = Line2D([], [], color='red')
        self.lineRSI_MED = Line2D([], [], color='white')
        self.lineRSI = Line2D([], [], color='orange')


        self.RSI.add_line(self.lineRSI_INF)
        self.RSI.add_line(self.lineRSI_SUP)
        self.RSI.add_line(self.lineRSI_MED)
        self.RSI.add_line(self.lineRSI)

        animation.TimedAnimation.__init__(self, fig, interval=20000, blit=True)

    def _draw_frame(self, framedata):
        self.axBase.clear
        self.RSI.clear
        self.VOLUM.clear

        pricedata = readData()


        # SMA
        x = pricedata['date'].index
        self.linePrice.set_data(x, pricedata['bidclose'])
        self.lineSMA200.set_data(x, pricedata['ema'])
        self.lineSMA400.set_data(x, pricedata['ema_slow'])
        self.ema_res1.set_data(x, pricedata['ema_res1'])
        self.ema_res2.set_data(x, pricedata['ema_res2'])
        self.ema_res3.set_data(x, pricedata['ema_res3'])
    
        # # Plot results
        #self.axPicsLinePriceHigh.set_data(x, pricedata['bidhigh'])
        #self.axPicsLinePriceLow.set_data(x, pricedata['bidlow'])


        # RSI
        pricedata['RSI_INF'] = 30
        pricedata['RSI_SUP'] = 70
        pricedata['RSI_MED'] = 50

        self.lineRSI_INF.set_data(x, pricedata['RSI_INF'])
        self.lineRSI_SUP.set_data(x, pricedata['RSI_SUP'])
        self.lineRSI_MED.set_data(x, pricedata['RSI_MED'])
        self.lineRSI.set_data(x, pricedata['RSI'])

        self.VOLUMLineVolum.set_data(x, pricedata['tickqty'])
        self.VOLUMLinePromedio.set_data(x, pricedata['tickqtySMA'])
        self.VOLUMFast.set_data(x, pricedata['tickqtySMAFast'])
        self.VOLUMLimit.set_data(x, pricedata['tickqtyLIMIT'])

        self.RSI.relim()
        self.RSI.autoscale_view()


        self.axBase.relim()
        self.axBase.autoscale_view()
        
        self.VOLUM.relim()
        self.VOLUM.autoscale_view()

        self._drawn_artists = [self.linePrice, self.lineSMA200,self.lineSMA400,self.ema_res1,self.ema_res2,self.ema_res3,
                               self.lineRSI_INF, self.lineRSI_SUP, self.lineRSI,self.lineRSI_MED,
                               self.VOLUMLineVolum, self.VOLUMLinePromedio,self.VOLUMFast,self.VOLUMLimit,
                               ]
       

    def new_frame_seq(self):
        return iter(range(self.t.size))

    def _init_draw(self):
        lines = [self.linePrice, self.lineSMA200, self.lineSMA400,self.ema_res1,self.ema_res2,self.ema_res3,
                 self.lineRSI_INF, self.lineRSI_SUP, self.lineRSI,self.lineRSI_MED,
                 self.VOLUMLineVolum, self.VOLUMLinePromedio,self.VOLUMFast,self.VOLUMLimit,
                 ]
        for l in lines:
            l.set_data([], [])
        


def start():
    ani = SubplotAnimation()
    # ani.save('test_sub.mp4')
    plt.show()

if __name__ == "__main__":
    start()