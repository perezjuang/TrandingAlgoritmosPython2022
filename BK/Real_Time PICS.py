import math
import fxcmpy
import time
import datetime as dt
from scipy import signal
import numpy as np
from pyti.simple_moving_average import simple_moving_average as ema
from pyti.relative_strength_index import relative_strength_index as rsi
from sqlalchemy import false
import Probabilidades.RegrsionLineal2 as regresionlineal2


token = 'cfc00f60a0f97eb0d837adf1b109c11f327421e3'

symbol = 'EUR/USD'
# Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8','D1', 'W1', or 'M1'.
timeframe = "m1"


file = symbol.replace("/", "_") + timeframe +".csv"



amount = 1
stop = -5
limit = 6

# Global Variables
pricedata = None
pricedata_sup = None
numberofcandles = 500

def GetConnection():
    return fxcmpy.fxcmpy(access_token=token, server="demo", log_level="error", log_file="zfxcm.log")

con = GetConnection()

numerErrors = 0

def RetryConection():
    global con
    try:
        if con.is_connected() == false:
            print("Restablising")
            con.close()
            con = GetConnection() 
        else:
            print("Is Conected")               
    except Exception as e:
        print("Ex Conecting Again Server Blocking!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(e)

def Prepare():
    global pricedata
    print("Requesting Initial Price Data...")
    pricedata = con.get_candles(symbol, period=timeframe, number=numberofcandles)
    print("Initial Price Data Received...")

def StrategyHeartBeat():
    getLatestPriceData()
    while True:
        currenttime = dt.datetime.now()
        if timeframe == "m1" and currenttime.second == 0 and getLatestPriceData():
            Update()
        elif timeframe == "m5" and currenttime.second == 0 and currenttime.minute % 5 == 0 and getLatestPriceData():
            Update()
            time.sleep(240)
        elif timeframe == "m15" and currenttime.second == 0 and currenttime.minute % 15 == 0 and getLatestPriceData():
            Update()
            time.sleep(840)
        elif timeframe == "m30" and currenttime.second == 0 and currenttime.minute % 30 == 0 and getLatestPriceData():
            Update()
            time.sleep(1740)
        elif currenttime.second == 0 and currenttime.minute == 0 and getLatestPriceData():
            Update()
            time.sleep(3540)
        time.sleep(1)


def getLatestPriceData():
    global pricedata
    global numerErrors
    try:
        # Normal operation will update pricedata on first attempt
        new_pricedata = con.get_candles(symbol, period=timeframe, number=numberofcandles)
        if new_pricedata.size != 0:
            if new_pricedata.index.values[len(new_pricedata.index.values)-1] != pricedata.index.values[len(pricedata.index.values)-1]:
                pricedata = new_pricedata
                numerErrors = 0
                return True
        
            # If data is not available on first attempt, try up to 3 times to update pricedata    
            counter = 0 
            while new_pricedata.index.values[len(new_pricedata.index.values)-1] == pricedata.index.values[len(pricedata.index.values)-1] and counter < 3:
                print("No updated prices found, trying again in 30 seconds...")
                counter+=1
                time.sleep(30)
                new_pricedata = con.get_candles(symbol, period=timeframe, number=numberofcandles)

            if new_pricedata.index.values[len(new_pricedata.index.values)-1] != pricedata.index.values[len(pricedata.index.values)-1]:
                pricedata = new_pricedata
                return True
            else:
                print("No Price Recived 1 Retry in 10 Seconds")
                time.sleep(10)
                return False
        else:
            print("No Price Recived 2 Retry en 10 Seconds")
            time.sleep(10)
            return False
        
    except Exception as e:
        print(e)
        print("Restablising")
        RetryConection()
        return False


def Update():

    print(str(dt.datetime.now()) + " " + timeframe + " Bar Closed - Running Update Function...")

    # HMA fast and slow calculation
    pricedata['ema'] = ema(pricedata['bidclose'], 10)
    pricedata['ema_slow'] = ema(pricedata['bidclose'], 100)
    pricedata['sell'] = (pricedata['bidclose'] < pricedata['ema'])
    pricedata['buy'] = (pricedata['bidclose'] > pricedata['ema'])

    iFastSMA = pricedata['ema']
    iSlowSMA = pricedata['ema_slow']

    # Find local peaks
    pricedata['min'] = pricedata.iloc[signal.argrelextrema(pricedata['bidclose'].values, np.less_equal, order=10)[0]]['bidclose']
    pricedata['max'] = pricedata.iloc[signal.argrelextrema(pricedata['bidclose'].values, np.greater_equal, order=10)[0]]['bidclose']

    # RSI
    pricedata['RSI'] = rsi(pricedata['bidclose'], 10)
    pricedata['RSI_sell'] = (pricedata['RSI'] > 70)
    pricedata['RSI_buy'] = (pricedata['RSI'] < 30)
    #pricedata['rsi_signal_sell'] = np.where(pricedata['RSI'] > pricedata['RSI'], 1, 0)
    #pricedata['rsi_signal_buy'] = np.where(pricedata['hma_fast'] > pricedata['RSI'], 1, 0)



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

  # Find local peaks
     # ************* Calcular la poscion Relativa MINxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    for index, row in pricedata.iterrows():
        if (math.isnan(pricedata.loc[index, 'min']) != True):
            pricedata.loc[index, 'min_pred'] = pricedata.loc[index, 'y']


    #PREDIC MIN df['a_col'].ffill(method='ffill')
    pricedata['y_pred_min'] = pricedata['min_pred']
    #Fill Firs pic with the firs pic
    pricex = pricedata['min_pred'].dropna()
    pricedata['y_pred_min'].iloc[len(pricedata) - 1] = pricex.iloc[len(pricex) - 1]  #pricex.iloc[len(pricex) - 1] #pricex.iloc[0]        
    #Fill nan wity the last value
    pricedata['y_pred_min'] =  pricedata['y_pred_min'].fillna(method='bfill')

    regresionLineal_xx = np.array(pricedata['x'].values)
    regresionLineal_yy = np.array(pricedata['y_pred_min'].values)
    regresionLineal_bb = regresionlineal2.estimate_b0_b1(regresionLineal_xx, regresionLineal_yy)
    y_pred_sup = regresionLineal_bb[0] + regresionLineal_bb[1] * regresionLineal_xx
    pricedata['y_pred_min'] = y_pred_sup


    # ************* Calcular la poscion Relativa MAXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    for index, row in pricedata.iterrows():
        if (math.isnan(pricedata.loc[index, 'max']) != True):
            pricedata.loc[index, 'max_pred'] = pricedata.loc[index, 'y']

    #PREDIC MAX df['a_col'].ffill(method='ffill')
    pricedata['y_pred_max'] = pricedata['max_pred']
    #Fill Firs pic with the firs pic
    pricex = pricedata['y_pred_max'].dropna()
    pricedata['y_pred_max'].iloc[len(pricedata) - 1] = pricex.iloc[len(pricex) - 1]  # pricex.iloc[len(pricex) - 1] #pricex.iloc[0]
    #Fill nan wity the last value
    pricedata['y_pred_max'] =  pricedata['y_pred_max'].fillna(method='bfill')

    regresionLineal_xx = np.array(pricedata['x'].values)
    regresionLineal_yy = np.array(pricedata['y_pred_max'].values)
    regresionLineal_bb = regresionlineal2.estimate_b0_b1(regresionLineal_xx, regresionLineal_yy)
    y_pred_sup = regresionLineal_bb[0] + regresionLineal_bb[1] * regresionLineal_xx
    pricedata['y_pred_max'] = y_pred_sup



    lv_Tendency_max = "Rango"
    if  pricedata.iloc[1]['y_pred_max'] > pricedata.iloc[len(pricedata) - 1]['y_pred_max']:
        lv_Tendency_max = "Bajista"
    elif  pricedata.iloc[1]['y_pred_max'] < pricedata.iloc[len(pricedata) - 1]['y_pred_max']:
        lv_Tendency_max = "Alcista"




    lv_Tendency_min = "Rango"
    if  pricedata.iloc[1]['y_pred_min'] > pricedata.iloc[len(pricedata) - 1]['y_pred_min']:
        lv_Tendency_min = "Bajista"
    elif pricedata.iloc[1]['y_pred_min'] < pricedata.iloc[len(pricedata) - 1]['y_pred_min'] :            
        lv_Tendency_min = "Alcista"


    if  lv_Tendency_max == "Alcista" and lv_Tendency_min == "Alcista":
        lv_Tendency = "Alcista"
    elif lv_Tendency_min == "Bajista" and lv_Tendency_max == "Bajista":
         lv_Tendency = "Bajista"
    else:
        lv_Tendency = "Rango"


    #Zona de Operacion Compra
    operacion = "Media"
    if pricedata.iloc[len(pricedata) - 1]['y_pred_min'] > pricedata.iloc[len(pricedata) - 1]['y']:
        operacion = "Compra"
    elif pricedata.iloc[len(pricedata) - 1]['y_pred_max'] < pricedata.iloc[len(pricedata) - 1]['y']:
        operacion = "Venta"



    print("	  Datos Bot ******************************! ") 
    print(lv_Tendency) 
    print("	  Datos Bot ******************************! ") 

    # TRADING LOGIC
    if crossesOver(iFastSMA, iSlowSMA) and lv_Tendency == "Alcista":#if  math.isnan(pricedata['min'].iloc[-1]) != True:#  \
         #and  pricedata['buy'].iloc[-2]:# == True or pricedata['buy'].iloc[-3] == True or pricedata['buy'].iloc[-4] == True ) \
         #and operacion == "Compra": # and lv_Tendency == "Bajista"::
            print("	  BUY SIGNAL! ") 
            if countOpenTrades("B") == 0 :
                if countOpenTrades("S") > 0:
                    exit("S")
                print("	  Opening Buy Trade...")
                enter("B")
      

        # TRADING LOGIC
    if crossesUnder(iFastSMA, iSlowSMA) and lv_Tendency == "Bajista":
    #if math.isnan(pricedata['max'].iloc[-1]) != True:# \
        #and  pricedata['sell'].iloc[-2]:# == True or pricedata['sell'].iloc[-3] == True or pricedata['sell'].iloc[-4] == True ) \
        #and operacion == "Venta": # and lv_Tendency == "Alcista":
            print("	  SELL SIGNAL!")
            if countOpenTrades("S") == 0:
                if countOpenTrades("B") > 0:
                    exit("B")            
                print("	  Opening Sell Trade...")
                enter("S")
      

    pricedata.to_csv(file)
    print(str(dt.datetime.now()) + " " +
          timeframe + " Update Function Completed.\n")


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