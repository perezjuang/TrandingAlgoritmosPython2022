import datetime as dt
import os
import time
import fxcmpy
from pyti.relative_strength_index import relative_strength_index as rsi
import pyti.stochastic as sto
import pandas as pd
import numpy as np
from scipy import signal
import Probabilidades.RegrsionLineal2 as regresionlineal2
token = 'c4a946e1a8a68558e71877bcf5b25014a3fe40d3'

fileName = str(os.path.basename(__file__))
fileName = fileName.replace(".py", "")
fileName = fileName.replace("Real_Time_", "")
symbol = fileName.replace("_", "/")

# Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8','D1', 'W1', or 'M1'.
timeframe = "m1"

file = symbol.replace("/", "_") + ".csv"


# Global Variables
amount = 1
stop = -8
limit = 30

#Volumen
tickqtyLIMIT = 400


pricedata = None
pricedata_sup = None
numberofcandles = 2000

DOWNWARD_TREND = 'DOWNWARD-TREND'
UPWARD_TREND = 'UPWARD-TREND'

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
        exec(open('Real_Time_EUR_USD.py').read())
        print("Rrestarting... Done")
        raise SystemExit


def Prepare():
    global pricedata
    print("Requesting Initial Price Data...")
    pricedata = con.get_candles(
        symbol, period=timeframe, number=numberofcandles)
    print("Initial Price Data Received...")


def StrategyHeartBeat():
    print("Starting.....")
    while True:
        currenttime = dt.datetime.now()
        if timeframe == "m1" and currenttime.second == 0:
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
        new_pricedata = con.get_candles(
            symbol, period=timeframe, number=numberofcandles)
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
    print(str(dt.datetime.now()) + " " + timeframe + " Bar Closed " + symbol)

    d = {'bidhigh': pricedata['bidhigh'],
         'bidlow': pricedata['bidlow'],
         'bidclose': pricedata['bidclose'],
         'bidopen': pricedata['bidopen'], 
         'tickqty': pricedata['tickqty']         
         }
    df = pd.DataFrame(data=d)
    df = df.assign(row_count=range(len(df)))
    df.index = df['row_count'].values

    # HMA fast and slow calculation
    df['ema'] = df['bidclose'].ewm(span=5).mean()
    df['ema_slow'] = df['bidclose'].ewm(span=5).mean()
    df['ema_res1'] = df['bidclose'].ewm(span=5).mean()
    df['ema_res2'] = df['bidclose'].ewm(span=5).mean()
    df['ema_res3'] = df['bidclose'].ewm(span=5).mean()

    df['rsi'] = rsi(df['bidclose'], 15)
    df['sto_k'] = sto.percent_k(df['bidclose'], 10)
    df['sto_d'] = sto.percent_d(df['bidclose'], 10)
    df['sto_k'] = df['sto_k'].ewm(span=10).mean()
    df['sto_d'] = df['sto_d'].ewm(span=10).mean()
    # Volumen trend
    #df['tickqtyLIMIT'] = tickqtyLIMIT
    #df['volumHight'] = np.where((df['tickqty'] > df['tickqtyLIMIT']), 1, 0)

    df['value1'] = 1

    # Find local peaks
    df['peaks_min'] = df.iloc[signal.argrelextrema(df['bidclose'].values,np.less_equal, order=20)[0]]['value1']
    df['peaks_max'] = df.iloc[signal.argrelextrema(df['bidclose'].values,np.greater_equal,order=20)[0]]['value1']



    #Find Difference in PIPS AND VOLUMEN
    for index, row in df.iterrows():        
        if df.loc[index, 'peaks_max'] == 1:
            iRV = index
            while (iRV > 1):
                iRV = iRV - 1
                if df.loc[iRV, 'peaks_min'] == 1:
                      df.loc[index, 'volumenPipsDiference'] =  ( abs ( df.loc[index, 'bidclose'] - df.loc[iRV, 'bidclose'] ) )
                      iRV = 1

    for index, row in df.iterrows():        
        if df.loc[index, 'peaks_min'] == 1:
            iRV = index
            while (iRV > 1):
                iRV = iRV - 1
                if df.loc[iRV, 'peaks_max'] == 1:
                      df.loc[index, 'volumenPipsDiference'] = ( abs ( df.loc[index, 'bidclose'] - df.loc[iRV, 'bidclose'] ) )
                      iRV = 1


    df['volumenPipsDiference'] = df['volumenPipsDiference'].fillna(method="ffill")
    df['volumLimitOperation'] = 0.002
    df['volumEnableOperation'] = np.where( (df['volumenPipsDiference'] >= df['volumLimitOperation']) , 1, 0)

    #Find Price after pic if in correct position
    df['priceInPositionSell'] = 0
    for index, row in df.iterrows():
        try:
             if df.loc[index, 'peaks_max'] == 1  and df.loc[index + 5, 'bidclose'] < df.loc[index + 5, 'ema'] and df.loc[index, 'volumEnableOperation'] == 1:  
                    df.loc[index, 'priceInPositionSell'] = 1
             elif df.loc[index, 'peaks_min'] == 1  and df.loc[index + 5, 'bidclose'] > df.loc[index + 5, 'ema'] and df.loc[index, 'volumEnableOperation'] == 1: 
                    df.loc[index, 'priceInPositionBuy'] = 1
        except:
            print("peaks: In Validation")



  

    df['sell'] = np.where( (df['priceInPositionSell'] == 1) , 1, 0)
    
    # Close Strategy Operation Sell
    operationActive = False
    for index, row in df.iterrows():
        if df.loc[index, 'sell'] == 1:
            operationActive = True
        if operationActive == True:
            df.loc[index, 'sell'] = 1
        if df.loc[index, 'peaks_min'] == 1:
            operationActive = False

    df['zone_sell'] = df['sell'].diff()

    if df['zone_sell'][len(df) - 6] == -1:
            if countOpenTrades("S") > 0:
                exit("S")


    if df['zone_sell'][len(df) - 6] == 1:
        print("	  SELL SIGNAL!")
        if countOpenTrades("S") == 0:
            if countOpenTrades("B"):
                exit("B")
            print("	  Opening Sell Trade...")
            enter("S")

    # ***********************************************************
    # * Estrategy  BUY
    # ***********************************************************
    df['buy'] = np.where( (df['priceInPositionBuy'] == 1)

                         , 1, 0)


    # Close Strategy Operation Sell
    operationActive = False
    for index, row in df.iterrows():
        if df.loc[index, 'buy'] == 1:
            operationActive = True
        if operationActive == True:
            df.loc[index, 'buy'] = 1
        if df.loc[index, 'peaks_max'] == 1:
            operationActive = False



    df['zone_buy'] = df['buy'].diff()



    if df['zone_buy'][len(df) - 6] == -1:
        if countOpenTrades("B") > 0:
            exit("B")

    if df['zone_buy'][len(df) - 6] == 1:
        print("	  BUY SIGNAL! ")
        if countOpenTrades("B") == 0:
            if countOpenTrades("S") > 0:
                exit("S")
            print("	  Opening Buy Trade...")
            enter("B")

    df.to_csv(file)
    print(str(dt.datetime.now()) + " " + timeframe +
          " Update Function Completed. " + symbol + "\n")


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


Prepare()  # Initialize strategy
StrategyHeartBeat()  # Run strategy
