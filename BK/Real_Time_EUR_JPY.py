import datetime as dt
import os
import time
import fxcmpy
from pyti.simple_moving_average import simple_moving_average as sma
from pyti.relative_strength_index import relative_strength_index as rsi
from numpy import mean
import pandas as pd
import numpy as np

token = 'cfc00f60a0f97eb0d837adf1b109c11f327421e3'

fileName = str(os.path.basename(__file__))
fileName = fileName.replace(".py", "")
fileName = fileName.replace("Real_Time_", "")
symbol = fileName.replace("_", "/")

# Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8','D1', 'W1', or 'M1'.
timeframe = "m1"

file = symbol.replace("/", "_") + ".csv"

amount = 1
stop = -10
limit = 20

# Global Variables
pricedata = None
pricedata_sup = None
numberofcandles = 400
tickqtyLIMIT = 250


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

    print(str(dt.datetime.now()) + " " + timeframe +
          " Bar Closed - Running Update Function...")


    df = pd.read_csv('EUR_USD.csv')

    # Define our pip cost and lot size
    pip_cost = 1
    lot_size = 10

    # Define EMA Fast / Slow parameters
    fast = 5
    slow = 10
    big1slow = 15
    big2slow = 20

    # HMA fast and slow calculation
    df['hma_fast'] = df['bidclose'].ewm(span=fast).mean()
    df['hma_slow'] = df['bidclose'].ewm(span=slow).mean()
    df['hma_big1slow'] = df['bidclose'].ewm(span=big1slow).mean()
    df['hma_big2slow'] = df['bidclose'].ewm(span=big2slow).mean()
    df['value1'] = 1
    # Find local peaks
    df['peaks_min'] = df.iloc[signal.argrelextrema(df['bidclose'].values, np.less, order=20)[0]]['value1']
    df['peaks_max'] = df.iloc[signal.argrelextrema(df['bidclose'].values, np.greater, order=20)[0]]['value1']

    # Volumen trend
    df['tickqtyLIMIT'] = 150
    df['tickqty_fast'] = sma(df['tickqty'],fast)
    df['volumHight'] = np.where( (df['tickqty_fast'] > df['tickqtyLIMIT'] ) , 1, 0)


    df['sell'] = np.where( (df['peaks_max'] == 1) 
                        & (df['volumHight'] == 1)
                        & (df['hma_fast'] > df['hma_slow'])
                        & (df['hma_slow'] > df['hma_big1slow'])
                        & (df['hma_big1slow'] > df['hma_big2slow']), 1, 0)


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
                        & (df['volumHight'] == 1)
                        & (df['hma_fast'] < df['hma_slow'])
                        & (df['hma_slow'] < df['hma_big1slow'])
                        & (df['hma_big1slow'] < df['hma_big2slow']), 1, 0)



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

    if df['OperationSell'][len(df) - 1]:
        print("	  SELL SIGNAL!")
        if countOpenTrades("S") == 0:
            if countOpenTrades("B"):
                exit("B")
            print("	  Opening Sell Trade...")
            enter("S")

    # ***********************************************************
    # * Estrategy  BUY
    # ***********************************************************

    df['buy'] = df.apply(lambda x: x.ema >= x.ema_slow
                                       and x.ema >= x.ema_res1
                                       and x.ema >= x.ema_res2
                                       and x.ema >= x.ema_res3,
                                       axis=1)
    df['zone_buy'] = df['buy'].diff()

    # Validate if first candle is in RSI ZONE
    df['OpenOperationBuy'] = df.apply(lambda x: x.zone_buy == True
                                                    and x.buy == True
                                                    and x.VolumenTrend == True,
                                                    axis=1)
    df['OperationBuy'] = df['OpenOperationBuy'].diff()

    if df['OperationBuy'][len(df) - 1]:
        print("	  BUY SIGNAL! ")
        if countOpenTrades("B") == 0:
            if countOpenTrades("S") > 0:
                exit("S")
            print("	  Opening Buy Trade...")
            enter("B")

    # datatoprint = pricedata[['RSI', 'sell', 'zone_sell', 'RSI_uppval',
     #                        'zone_upp_rsi', 'buy', 'zone_buy', 'RSI_subval', 'zone_sub_rsi']]
    # datatoprint.to_csv(file)
    df.to_csv(file)
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


Prepare()  # Initialize strategy
StrategyHeartBeat()  # Run strategy
