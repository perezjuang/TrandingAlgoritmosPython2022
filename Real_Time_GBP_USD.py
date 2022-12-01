import datetime as dt
import time
import fxcmpy
from pyti.exponential_moving_average import exponential_moving_average as ema
from pyti.relative_strength_index import relative_strength_index as rsi

token = 'cfc00f60a0f97eb0d837adf1b109c11f327421e3'

symbol = 'GBP/USD'
# Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8','D1', 'W1', or 'M1'.
timeframe = "m1"

file = symbol.replace("/", "_") + timeframe + ".csv"

amount = 1
stop = -8
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

    # HMA fast and slow calculation
    pricedata['ema'] = ema(pricedata['bidclose'], 3)
    pricedata['ema_slow'] = ema(pricedata['bidclose'], 20)
    pricedata['ema_res1'] = ema(pricedata['bidclose'], 25)
    pricedata['ema_res2'] = ema(pricedata['bidclose'], 50)

    # ***********************************************************
    # * RSI
    # ***********************************************************
    pricedata['RSI'] = rsi(pricedata['bidclose'], 15)
    pricedata['RSI_uppval'] = (pricedata['RSI'] >= 65) & (
        pricedata['RSI'] <= 100)
    pricedata['RSI_subval'] = (
        pricedata['RSI'] <= 35) & (pricedata['RSI'] >= 0)




    pricedata['sell'] = (pricedata['ema'] < pricedata['ema_slow']) & (pricedata['ema'] < pricedata['ema_res1']) & (
        pricedata['ema'] < pricedata['ema_res2'])

    pricedata['zone_sell'] = pricedata['sell'].diff()

    pricedata['buy'] = (pricedata['ema'] > pricedata['ema_slow']) & (pricedata['ema'] > pricedata['ema_res1']) & (
        pricedata['ema'] > pricedata['ema_res2']) 

    pricedata['zone_buy'] = pricedata['buy'].diff()

    trendZoneSubvaluation = (pricedata['RSI_subval'][len(pricedata) - 1] or pricedata['RSI_subval'][len(pricedata) - 2] or pricedata['RSI_subval'][len(pricedata) - 3] or pricedata['RSI_subval'][len(pricedata) - 4] or pricedata['RSI_subval'][len(pricedata) - 5] or pricedata['RSI_subval'][len(pricedata) - 6] or pricedata['RSI_subval'][len(pricedata) - 7] or pricedata['RSI_subval'][len(pricedata) - 8] or pricedata['RSI_subval'][len(pricedata) - 9] or pricedata['RSI_subval'][len(pricedata) - 10]) 
    trendZoneOvervaluation = (pricedata['RSI_uppval'][len(pricedata) - 1] or pricedata['RSI_uppval'][len(pricedata) - 2] or pricedata['RSI_uppval'][len(pricedata) - 3] or pricedata['RSI_uppval'][len(pricedata) - 4] or pricedata['RSI_uppval'][len(pricedata) - 5] or pricedata['RSI_uppval'][len(pricedata) - 6]  or pricedata['RSI_uppval'][len(pricedata) - 7]  or pricedata['RSI_uppval'][len(pricedata) - 8]  or pricedata['RSI_uppval'][len(pricedata) - 9]  or pricedata['RSI_uppval'][len(pricedata) - 10])

    if trendZoneOvervaluation:
        print("	  Overvaluation zone")
    if trendZoneSubvaluation:
        print("	  Subvaluation zone")


    # TRADING LOGIC BUY OPEN OPERATIONS
    if trendZoneSubvaluation :        
        if pricedata['zone_buy'][len(pricedata) - 1] and pricedata['buy'][len(pricedata) - 1]:
            print("	  Uptrend zone")
            print("	  BUY SIGNAL! ")
            if countOpenTrades("B") == 0:
                if countOpenTrades("S") > 0 and pricedata['ema'][len(pricedata) - 1] < pricedata['ema_slow'][len(pricedata) - 1]:
                    exit("S")
                print("	  Opening Buy Trade...")
                enter("B")

    # TRADING LOGIC  BUY OPEN OPERATIONS
    if trendZoneOvervaluation:
        if pricedata['zone_sell'][len(pricedata) - 1] and pricedata['sell'][len(pricedata) - 1]  :
            print("	  Downtrend zone")
            print("	  SELL SIGNAL!")
            if countOpenTrades("S") == 0:
                if countOpenTrades("B") > 0 and pricedata['ema'][len(pricedata) - 1] > pricedata['ema_slow'][len(pricedata) - 1]:
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


Prepare()  # Initialize strategy
StrategyHeartBeat()  # Run strategy