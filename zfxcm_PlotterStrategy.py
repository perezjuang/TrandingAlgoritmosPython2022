import fxcmpy
from ast import If
import pandas as pd
import matplotlib.pyplot as plt
from dbOperations.database import Database
from pyti.simple_moving_average import simple_moving_average as sma
from pyti.relative_strength_index import relative_strength_index as rsi
from pyti.stochastic import percent_d as sto_percent_d
from pyti.stochastic import percent_k as sto_percent_k
from scipy import signal
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.animation as animation
import zfxcm_Global
import configparser
import math
import RegrsionLineal2 as regresionlineal2
config = configparser.ConfigParser()
config.read('RobotV5.ini')


# This function runs once at the beginning of the strategy to create price/indicator streams
time_frame_operations = config['timeframe']
timeframe = time_frame_operations['timeframe']

symbol = time_frame_operations['symbol']

numberofcandlesinview = time_frame_operations['numberofcandlesinview']
fast_sma_periods = time_frame_operations['fast_sma_periods']
slow_sma_periods = time_frame_operations['slow_sma_periods']

db = Database()
plt.style.use('dark_background')


class SubplotAnimation(animation.TimedAnimation):
    def __init__(self):

        fig = plt.figure()

        self.axBase = fig.add_subplot(2, 1, 1)
        self.RSI = fig.add_subplot(2, 1, 2)
        #self.STO = fig.add_subplot(3, 1, 3)

        self.t = np.linspace(0, 80, 400)
        self.x = np.cos(2 * np.pi * self.t / 10.)
        self.y = np.sin(2 * np.pi * self.t / 10.)
        self.z = 10 * self.t

        self.axBase.set_xlabel('Date')
        self.axBase.set_ylabel('Price Move')
        self.linePrice = Line2D([], [], color='white')
        self.lineSMA10 = Line2D([], [], color='green')
        self.lineSMA30 = Line2D([], [], color='red')

        self.axBase.add_line(self.linePrice)
        self.axBase.add_line(self.lineSMA10)
        self.axBase.add_line(self.lineSMA30)

        self.axPicsLinePriceHigh, = self.axBase.plot(
            [], [], linestyle='dotted', color='gray')
        self.axPicsLinePriceLow, = self.axBase.plot(
            [], [], linestyle='dotted', color='gray')
        self.axPicsLineMAX, = self.axBase.plot([], [], '.', color='green')
        self.axPicsLineMIN, = self.axBase.plot([], [], '.', color='red')

        self.axBase.add_line(self.axPicsLinePriceHigh)
        self.axBase.add_line(self.axPicsLinePriceLow)
        self.axBase.add_line(self.axPicsLineMAX)
        self.axBase.add_line(self.axPicsLineMIN)

        self.RSI.set_xlabel('DATE')
        self.RSI.set_ylabel('RSI')
        self.lineRSI_INF = Line2D([], [], color='red')
        self.lineRSI_SUP = Line2D([], [], color='red')
        self.lineRSI = Line2D([], [], color='orange')
        self.RSI.add_line(self.lineRSI_INF)
        self.RSI.add_line(self.lineRSI_SUP)
        self.RSI.add_line(self.lineRSI)

       # self.STO.set_xlabel('Date')
       # self.STO.set_ylabel('STO')
        #self.STO_INF = Line2D([], [], color='red')
        #self.STO_SUP = Line2D([], [], color='red')
        #self.STO_K = Line2D([], [], color='green')
        #self.STO_D = Line2D([], [], color='red')
        # self.STO.add_line(self.STO_INF)
        # self.STO.add_line(self.STO_SUP)
        # self.STO.add_line(self.STO_D)
        # self.STO.add_line(self.STO_K)

        animation.TimedAnimation.__init__(self, fig, interval=5000, blit=True)

    def _draw_frame(self, framedata):

        pricedata = db.getData(timeframe='m1')
        #pricedata =  pricedata.tail(int(numberofcandlesinview))
        # SMA
        self.linePrice.set_data(pricedata['date'], pricedata['bidclose'])
        self.lineSMA10.set_data(
            pricedata['date'], sma(pricedata['bidclose'], 10))
        self.lineSMA30.set_data(
            pricedata['date'], sma(pricedata['bidclose'], 30))

        # Find local peaks
        pricedata['min'] = pricedata.iloc[signal.argrelextrema(sma(pricedata['bidlow'], 3), np.less,
                                                               order=100)[0]]['bidlow']

        pricedata['max'] = pricedata.iloc[signal.argrelextrema(sma(pricedata['bidhigh'], 3), np.greater,
                                                               order=100)[0]]['bidhigh']

        # Plot results
        self.axPicsLinePriceHigh.set_data(
            pricedata['date'], sma(pricedata['bidhigh'], 3))
        self.axPicsLinePriceLow.set_data(
            pricedata['date'], sma(pricedata['bidlow'], 3))

        self.axPicsLineMAX.set_data(pricedata['date'], pricedata['max'])
        self.axPicsLineMIN.set_data(pricedata['date'], pricedata['min'])

        self.axBase.relim()
        self.axBase.autoscale_view()

        # RSI
        pricedata['RSI_INF'] = 20
        pricedata['RSI_SUP'] = 80
        pricedata['RSI'] = rsi(pricedata['bidclose'], 15)

        self.lineRSI_INF.set_data(pricedata['date'], pricedata['RSI_INF'])
        self.lineRSI_SUP.set_data(pricedata['date'], pricedata['RSI_SUP'])
        self.lineRSI.set_data(pricedata['date'], pricedata['RSI'])

        self.RSI.relim()
        self.RSI.autoscale_view()

        # Stochasticsto
        k_period = 15
        d_period = 5
        pricedata['STO_INF'] = 20
        pricedata['STO_SUP'] = 80

        #pricedata['n_high'] = pricedata['bidhigh'].rolling(k_period).max()
        #pricedata['n_low'] = pricedata['bidlow'].rolling(k_period).min()
        #pricedata['STO_K'] = (pricedata['bidclose'] - pricedata['n_low']) * 100 / (pricedata['n_high'] - pricedata['n_low'])
        #pricedata['STO_D'] = pricedata['STO_K'].rolling(d_period).mean()
        #pricedata['STO_K'] = sto_percent_k(pricedata['bidclose'],period=k_period)
        #pricedata['STO_D'] = sto_percent_d(pricedata['bidclose'],period=d_period)

        #self.STO_INF.set_data(pricedata['date'], pricedata['STO_INF'])
        #self.STO_SUP.set_data(pricedata['date'], pricedata['STO_SUP'])
        #self.STO_D.set_data(pricedata['date'], pricedata['STO_D'])
        #self.STO_K.set_data(pricedata['date'], pricedata['STO_K'])
        #self.STO_D.set_data( sto_percent_k(pricedata['bidclose'],period=k_period))
        #self.STO_K.set_data( sto_percent_d(pricedata['bidclose'],period=d_period))

        # self.STO.relim()
        # self.STO.autoscale_view()

        # ***********************************************************
        # *  Regresion al precio de cierre las velas ================
        # ***********************************************************
        pricedata['x'] = np.arange(len(pricedata))

        # ************* Calcular la poscion Relativa Y
        for index, row in pricedata.iterrows():
            pricedata.loc[index, 'y'] = int('{:.5f}'.format((pricedata.loc[index, 'bidclose'])).replace('.', ''))
        max_value = max(np.array(pricedata['y'].values))
        min_value = min(np.array(pricedata['y'].values))
        for index, row in pricedata.iterrows():
            value = pricedata.loc[index, 'y'] - min_value
            NewPricePosition = ((value * 100) / max_value) * 100
            pricedata.loc[index, 'y'] = NewPricePosition

        # ***********  Calcular la poscion Relativa X
        max_value = max(np.array(pricedata['x'].values))
        min_value = min(np.array(pricedata['x'].values))
        for index, row in pricedata.iterrows():
            value = pricedata.loc[index, 'x'] - min_value
            NewPricePosition = ((value * 100) / max_value)
            pricedata.loc[index, 'x'] = NewPricePosition

        regresionLineal_xx = np.array(pricedata['x'].values)
        regresionLineal_yy = np.array(pricedata['y'].values)

        regresionLineal_bb = regresionlineal2.estimate_b0_b1(regresionLineal_xx, regresionLineal_yy)
        y_pred_sup = regresionLineal_bb[0] + regresionLineal_bb[1] * regresionLineal_xx
        pricedata['y_pred'] = y_pred_sup

        if pricedata.iloc[len(pricedata) - 1]['y_pred'] < \
                pricedata.iloc[1]['y_pred'] and \
                pricedata.iloc[len(pricedata) - 1]['y_pred'] < \
                pricedata.iloc[1]['y_pred']:
            lv_Tendency = "Bajista"
        elif pricedata.iloc[len(pricedata) - 1]['y_pred'] > \
                pricedata.iloc[1]['y_pred'] and \
                pricedata.iloc[len(pricedata) - 1]['y_pred'] > \
                pricedata.iloc[1]['y_pred']:
            lv_Tendency = "Alcista"
        

        if math.isnan(pricedata['max'].iloc[-1]) != True  \
                or math.isnan(pricedata['max'].iloc[-2]) != True \
                or math.isnan(pricedata['max'].iloc[-3]) != True \
                or math.isnan(pricedata['max'].iloc[-4]) != True:

            openpositions = zfxcm_Global.con.get_open_positions(kind='list')
            counterBuy = 0
            counterSell = 0
            for position in openpositions:
                if position['currency'] == symbol:
                    if position['isBuy'] == True:
                        counterBuy += 1
                    elif position['isBuy'] == False:
                        counterSell += 1
            print("Venta --- ")
            if counterSell == 0:
                opentrade = zfxcm_Global.con.open_trade(symbol=symbol, is_buy=False, amount='1', time_in_force='GTC',
                                                        order_type='AtMarket', is_in_pips=True, limit=5, stop=-5)
                print(opentrade)

        elif math.isnan(pricedata['min'].iloc[-1]) != True     \
                or math.isnan(pricedata['min'].iloc[-2]) != True   \
                or math.isnan(pricedata['min'].iloc[-3]) != True   \
                or math.isnan(pricedata['min'].iloc[-4])!= True:
            openpositions = zfxcm_Global.con.get_open_positions(kind='list')
            counterBuy = 0
            counterSell = 0
            for position in openpositions:
                if position['currency'] == symbol:
                    if position['isBuy'] == True:
                        counterBuy += 1
                    elif position['isBuy'] == False:
                        counterSell += 1
            print("Compra --- ")
            if counterBuy == 0:
                opentrade = zfxcm_Global.con.open_trade(symbol=symbol, is_buy=True, amount='1', time_in_force='GTC',
                                                        order_type='AtMarket', is_in_pips=True, limit=5, stop=-5)
                print(opentrade)

        self._drawn_artists = [self.linePrice, self.lineSMA10, self.lineSMA30,
                               self.lineRSI_INF, self.lineRSI_SUP, self.lineRSI,
                               #self.STO_INF, self.STO_SUP, self.STO_D, self.STO_K,
                               self.axPicsLinePriceHigh, self.axPicsLinePriceLow, self.axPicsLineMAX, self.axPicsLineMIN,
                               ]

    def new_frame_seq(self):
        return iter(range(self.t.size))

    def _init_draw(self):
        lines = [self.linePrice, self.lineSMA10, self.lineSMA30,
                 self.lineRSI_INF, self.lineRSI_SUP, self.lineRSI,
                 #self.STO_INF, self.STO_SUP, self.STO_D, self.STO_K,
                 self.axPicsLinePriceHigh, self.axPicsLinePriceLow, self.axPicsLineMAX, self.axPicsLineMIN,
                 ]
        for l in lines:
            l.set_data([], [])


def start():
    ani = SubplotAnimation()
    # ani.save('test_sub.mp4')
    plt.show()


if __name__ == "__main__":
    start()
