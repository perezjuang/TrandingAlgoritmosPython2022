import datetime as dt
import time

import fxcmpy
import numpy as np
from pyti.exponential_moving_average import exponential_moving_average as ema
from pyti.relative_strength_index import relative_strength_index as rsi
from scipy import signal

import Probabilidades.RegrsionLineal2 as regresionlineal2

token = 'cfc00f60a0f97eb0d837adf1b109c11f327421e3'

symbol = 'EUR/USD'
# Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8','D1', 'W1', or 'M1'.
timeframe = "m1"

file = symbol.replace("/", "_") + timeframe + ".csv"

amount = 1
stop = -5
limit = 10

# Global Variables
pricedata = None
pricedata_sup = None
numberofcandles = 100

def GetConnection():
    return fxcmpy.fxcmpy(access_token=token, server="demo", log_level="error", log_file="zfxcm.log")

con = GetConnection()

def RetryConection():
    global con
    try:
        if con.is_connected():
            print("Restablising")
            con.close()
            con = GetConnection() 
        else:
            print("Is Conected")               
    except Exception as e:
        print("Ex Conecting Again Server Blocking!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(e)
        time.sleep(20)
        print("Rrestarting..")
        exec(open('Real_Time.py').read())
        print("Rrestarting... Done")
        raise SystemExit

def Prepare():
    global pricedata
    print("Requesting Initial Price Data...")
    pricedata = con.get_candles(symbol, period=timeframe, number=numberofcandles)
    print("Initial Price Data Received...")

def StrategyHeartBeat():
    print("Starting.....")
    while True:
        currenttime = dt.datetime.now()   
        if timeframe == "m5" and currenttime.second == 0:
            print("Prices Requesting " + timeframe + " - " + str(currenttime))  



        if timeframe == "m1" and currenttime.second == 0 and getLatestPriceData():   
            Update()
            time.sleep(1)
        elif timeframe == "m5" and currenttime.second == 0 and currenttime.minute % 5 == 0 and getLatestPriceData():
            Update()
            time.sleep(240)
        elif timeframe == "m15" and currenttime.second == 0 and currenttime.minute % 15 == 0 and getLatestPriceData():
            Update()
            time.sleep(840)
        elif timeframe == "m30" and currenttime.second == 0 and currenttime.minute % 30 == 0 and getLatestPriceData():
            Update()
            time.sleep(1740)
        elif timeframe == "H1" and currenttime.second == 0 and currenttime.minute == 0 and getLatestPriceData():
            Update()
            time.sleep(3540)
        time.sleep(1)


def getLatestPriceData():
    global pricedata
    try:
        # Normal operation will update pricedata on first attempt
        new_pricedata = con.get_candles(symbol, period=timeframe, number=numberofcandles)
        if new_pricedata.size != 0:
            if new_pricedata.index.values[len(new_pricedata.index.values)-1] != pricedata.index.values[len(pricedata.index.values)-1]:
                pricedata = new_pricedata
                return True
            else:
                print("No Price updated recived")
                return False
        else:
            print("No Price updated recived")
            return False
    except Exception as e:
        print(e)
        print("Restablising")
        RetryConection()
        return False


def Update():

    print(str(dt.datetime.now()) + " " + timeframe + " Bar Closed - Running Update Function...")

    # HMA fast and slow calculation
    pricedata['ema'] = ema(pricedata['bidclose'], 2)
    pricedata['ema_slow'] = ema(pricedata['bidclose'], 20)
    pricedata['ema_res1'] = ema(pricedata['bidclose'], 25)
    pricedata['ema_res2'] = ema(pricedata['bidclose'], 50)

    iFastSMA = pricedata['ema']
    iSlowSMA = pricedata['ema_slow']


    #if ( pricedata['RSI_sell'][len(pricedata) - 1] or pricedata['RSI_sell'][len(pricedata) - 1] ) \
    #and pricedata['ema'][len(pricedata) - 1]  > pricedata['ema_slow'][len(pricedata) - 1] \
    #    and pricedata['ema'][len(pricedata) - 1] > pricedata['ema_res1'][len(pricedata) - 1] and pricedata['ema_slow'][len(pricedata) - 1] > pricedata['ema_res1'][len(pricedata) - 1] \
    #        and pricedata['ema'][len(pricedata) - 1] > pricedata['ema_res2'][len(pricedata) - 1]:



    pricedata['sell'] = (pricedata['ema'] < pricedata['ema_slow']) & (pricedata['ema_slow'] < pricedata['ema_res1']) & (pricedata['ema_res1'] < pricedata['ema_res2']) 
    pricedata['position_operation_sell'] = pricedata['sell'].diff()

    pricedata['buy'] = ( pricedata['ema'] > pricedata['ema_slow']) & ( pricedata['ema_slow'] > pricedata['ema_res1'] ) & ( pricedata['ema_res1'] > pricedata['ema_res2'] )
    pricedata['position_operation_buy'] = pricedata['buy'].diff()



    # Find local peaks
    pricedata['min'] = pricedata.iloc[signal.argrelextrema(pricedata['ema'].values, np.less, order=5)[0]]['ema']
    pricedata['max'] = pricedata.iloc[signal.argrelextrema(pricedata['ema'].values, np.greater, order=5)[0]]['ema']



    # ***********************************************************
    # * RSI
    # ***********************************************************
    pricedata['RSI'] = rsi(pricedata['bidclose'], 10)
    pricedata['RSI_sell'] = (pricedata['RSI'] > 60)
    pricedata['RSI_buy'] = (pricedata['RSI'] < 40)

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

    # ***********  Calcular la regresion Lineal
    regresionLineal_xx = np.array(pricedata['x'].values)
    regresionLineal_yy = np.array(pricedata['y'].values)
    regresionLineal_bb = regresionlineal2.estimate_b0_b1(regresionLineal_xx, regresionLineal_yy)
    y_pred_sup = regresionLineal_bb[0] + regresionLineal_bb[1] * regresionLineal_xx
    pricedata['y_pred'] = y_pred_sup



    # ***********************************************************
    # *  Regresion al precio de cierre alto las velas =========
    # ***********************************************************
    pricedata['x'] = np.arange(len(pricedata))

    # ************* Calcular la poscion Relativa Y
    for index, row in pricedata.iterrows():
        pricedata.loc[index, 'y_bidhigh'] = int('{:.5f}'.format((pricedata.loc[index, 'bidhigh'])).replace('.', ''))

    max_value = max(np.array(pricedata['y_bidhigh'].values))
    min_value = min(np.array(pricedata['y_bidhigh'].values))
    for index, row in pricedata.iterrows():
        value = pricedata.loc[index, 'y_bidhigh'] - min_value
        NewPricePosition = ((value * 100) / max_value) * 100
        pricedata.loc[index, 'y_bidhigh'] = NewPricePosition

    # ***********  Calcular la poscion Relativa X
    max_value = max(np.array(pricedata['x'].values))
    min_value = min(np.array(pricedata['x'].values))
    for index, row in pricedata.iterrows():
        value = pricedata.loc[index, 'x'] - min_value
        NewPricePosition = ((value * 100) / max_value)
        pricedata.loc[index, 'x'] = NewPricePosition
    # ***********  Calcular la regresion Lineal
    regresionLineal_xx = np.array(pricedata['x'].values)
    regresionLineal_yy = np.array(pricedata['y_bidhigh'].values)
    regresionLineal_bb = regresionlineal2.estimate_b0_b1(regresionLineal_xx, regresionLineal_yy)
    y_pred_sup = regresionLineal_bb[0] + regresionLineal_bb[1] * regresionLineal_xx
    pricedata['y_pred_bidhigh'] = y_pred_sup






    # ***********************************************************
    # *  Regresion al precio de cierre bajo las velas =========
    # ***********************************************************
    pricedata['x'] = np.arange(len(pricedata))

    # ************* Calcular la poscion Relativa Y
    for index, row in pricedata.iterrows():
        pricedata.loc[index, 'y_bidlow'] = int('{:.5f}'.format((pricedata.loc[index, 'bidlow'])).replace('.', ''))

    max_value = max(np.array(pricedata['y_bidlow'].values))
    min_value = min(np.array(pricedata['y_bidlow'].values))
    for index, row in pricedata.iterrows():
        value = pricedata.loc[index, 'y_bidlow'] - min_value
        NewPricePosition = ((value * 100) / max_value) * 100
        pricedata.loc[index, 'y_bidlow'] = NewPricePosition

    # ***********  Calcular la poscion Relativa X
    max_value = max(np.array(pricedata['x'].values))
    min_value = min(np.array(pricedata['x'].values))
    for index, row in pricedata.iterrows():
        value = pricedata.loc[index, 'x'] - min_value
        NewPricePosition = ((value * 100) / max_value)
        pricedata.loc[index, 'x'] = NewPricePosition
    # ***********  Calcular la regresion Lineal
    regresionLineal_xx = np.array(pricedata['x'].values)
    regresionLineal_yy = np.array(pricedata['y_bidlow'].values)
    regresionLineal_bb = regresionlineal2.estimate_b0_b1(regresionLineal_xx, regresionLineal_yy)
    y_pred_sup = regresionLineal_bb[0] + regresionLineal_bb[1] * regresionLineal_xx
    pricedata['y_pred_bidlow'] = y_pred_sup



    # print( Debug Price/Indicators
    print( "Close Price: " + str(pricedata['bidclose'][len(pricedata) - 1])) 
    print( "Fast SMA: " + str(iFastSMA[len(iFastSMA) - 1])) 
    print( "Slow SMA: " + str(iSlowSMA[len(iSlowSMA) - 1])) 



    # TRADING LOGIC ema
    if ( pricedata['RSI_sell'][len(pricedata) - 1] or pricedata['RSI_sell'][len(pricedata) - 1] ) \
    and pricedata['ema'][len(pricedata) - 1]  > pricedata['ema_slow'][len(pricedata) - 1] \
        and pricedata['ema'][len(pricedata) - 1] > pricedata['ema_res1'][len(pricedata) - 1] and pricedata['ema_slow'][len(pricedata) - 1] > pricedata['ema_res1'][len(pricedata) - 1] \
            and pricedata['ema'][len(pricedata) - 1] > pricedata['ema_res2'][len(pricedata) - 1]:
            print("	  BUY SIGNAL! ") 
            if countOpenTrades("B") == 0 :
                if countOpenTrades("S") > 0 and pricedata['ema'][len(pricedata) - 1]  < pricedata['ema_slow'][len(pricedata) - 1]:
                    exit("S")
                print("	  Opening Buy Trade...")
                enter("B")
    else:
            print("BUY RSI-EMAS no estan en posicion " + str(pricedata['ema_slow'][len(pricedata) - 1]) + " > " + str(pricedata['ema_res1'][len(pricedata) - 1]) + " > " + str(pricedata['ema_res2'][len(pricedata) - 1]) + " - " ) 

      

    # TRADING LOGIC
    if ( pricedata['RSI_sell'][len(pricedata) - 1] or pricedata['RSI_sell'][len(pricedata) - 1] ) \
        and pricedata['ema'][len(pricedata) - 1]  < pricedata['ema_slow'][len(pricedata) - 1] \
          and pricedata['ema'][len(pricedata) - 1] < pricedata['ema_res1'][len(pricedata) - 1] and pricedata['ema_slow'][len(pricedata) - 1] < pricedata['ema_res1'][len(pricedata) - 1] \
            and pricedata['ema'][len(pricedata) - 1] < pricedata['ema_res2'][len(pricedata) - 1]:
            print("	  SELL SIGNAL!")
            if countOpenTrades("S") == 0:
                if countOpenTrades("B") > 0 and pricedata['ema'][len(pricedata) - 1]  > pricedata['ema_slow'][len(pricedata) - 1]:
                    exit("B")            
                print("	  Opening Sell Trade...")
                enter("S")
    else:
            print("SELL RSI-EMAS no estan en posicion " + str(pricedata['ema_slow'][len(pricedata) - 1]) + " < " + str(pricedata['ema_res1'][len(pricedata) - 1]) + " < " + str(pricedata['ema_res2'][len(pricedata) - 1]) + " - " ) 

      

    pricedata.to_csv(file)
    print(str(dt.datetime.now()) + " " +  timeframe + " Update Function Completed.\n")


def enter(BuySell):
    direction = True
    if BuySell == "S":
        direction = False
    try:
        opentrade = con.open_trade(symbol=symbol, is_buy=direction, amount=amount,
                                   time_in_force='GTC', order_type='AtMarket', is_in_pips=True, limit=limit, stop=stop)
    except:
        print("	  Error Opening Trade.")
    else:
        print("	  Trade Opened Successfully.")


def exit(BuySell=None):
    openpositions = con.get_open_positions(kind='list')
    isbuy = True
    if BuySell == "S":
        isbuy = False
    for position in openpositions:
        if position['currency'] == symbol:
            if BuySell is None or position['isBuy'] == isbuy:
                print("	  Closing tradeID: " + position['tradeId'])
                try:
                    closetrade = con.close_trade(
                        trade_id=position['tradeId'], amount=position['amountK'])
                except:
                    print("	  Error Closing Trade.")
                else:
                    print("	  Trade Closed Successfully.")


def countOpenTrades(BuySell=None):
    counter = 0
    try:
        openpositions = con.get_open_positions(kind='list')
        isbuy = True
        if BuySell == "S":
            isbuy = False
        for position in openpositions:
            if position['currency'] == symbol:
                if BuySell is None or position['isBuy'] == isbuy:
                    counter += 1
    except:
                    print("	  Error reading Trade.")
    return counter

# Returns true if stream1 crossed over stream2 in most recent candle, stream2 can be integer/float or data array

def crossesOver(stream1, stream2):
    if isinstance(stream2, int) or isinstance(stream2, float):
        if stream1[len(stream1) - 1] <= stream2:
            return False
        else:
            if stream1[len(stream1) - 2] > stream2:
                return False
            elif stream1[len(stream1) - 2] < stream2:
                return True
            else:
                x = 2
                while stream1[len(stream1) - x] == stream2:
                    x = x + 1
                if stream1[len(stream1) - x] < stream2:
                    return True
                else:
                    return False
    else:
        if stream1[len(stream1) - 1] <= stream2[len(stream2) - 1]:
            return False
        else:
            if stream1[len(stream1) - 2] > stream2[len(stream2) - 2]:
                return False
            elif stream1[len(stream1) - 2] < stream2[len(stream2) - 2]:
                return True
            else:
                x = 2
                while stream1[len(stream1) - x] == stream2[len(stream2) - x]:
                    x = x + 1
                if stream1[len(stream1) - x] < stream2[len(stream2) - x]:
                    return True
                else:
                    return False


# Returns true if stream1 crossed under stream2 in most recent candle, stream2 can be integer/float or data array
def crossesUnder(stream1, stream2):
    if isinstance(stream2, int) or isinstance(stream2, float):
        if stream1[len(stream1) - 1] >= stream2:
            return False
        else:
            if stream1[len(stream1) - 2] < stream2:
                return False
            elif stream1[len(stream1) - 2] > stream2:
                return True
            else:
                x = 2
                while stream1[len(stream1) - x] == stream2:
                    x = x + 1
                if stream1[len(stream1) - x] > stream2:
                    return True
                else:
                    return False
    else:
        if stream1[len(stream1) - 1] >= stream2[len(stream2) - 1]:
            return False
        else:
            if stream1[len(stream1) - 2] < stream2[len(stream2) - 2]:
                return False
            elif stream1[len(stream1) - 2] > stream2[len(stream2) - 2]:
                return True
            else:
                x = 2
                while stream1[len(stream1) - x] == stream2[len(stream2) - x]:
                    x = x + 1
                if stream1[len(stream1) - x] > stream2[len(stream2) - x]:
                    return True
                else:
                    return False



Prepare()  # Initialize strategy
StrategyHeartBeat()  # Run strategy