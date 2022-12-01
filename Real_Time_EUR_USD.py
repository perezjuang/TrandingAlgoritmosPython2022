import datetime as dt
import time
import fxcmpy
from pyti.simple_moving_average import simple_moving_average as sma
from pyti.relative_strength_index import relative_strength_index as rsi
from numpy import mean

token = 'cfc00f60a0f97eb0d837adf1b109c11f327421e3'

symbol = 'EUR/USD'
# Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8','D1', 'W1', or 'M1'.
timeframe = "m1"

file = symbol.replace("/", "_") + timeframe + ".csv"

amount = 1
stop = -10
limit = 15

# Global Variables
pricedata = None
pricedata_sup = None
numberofcandles = 300


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

    # HMA fast and slow calculation
    pricedata['ema'] = sma(pricedata['bidclose'], 3)
    pricedata['ema_slow'] = sma(pricedata['bidclose'], 30)
    pricedata['ema_res1'] = sma(pricedata['bidclose'], 50)
    pricedata['ema_res2'] = sma(pricedata['bidclose'], 80)
    pricedata['ema_res3'] = sma(pricedata['bidclose'], 100)
    pricedata['tickqtySMAFast'] = sma(pricedata['tickqty'], 10)
    pricedata['tickqtySMA'] = sma(pricedata['tickqty'], 100)

   

    

    # ***********************************************************
    # * RSI
    # ***********************************************************
    pricedata['RSI'] = rsi(pricedata['bidclose'], 15)
    pricedata['RSI_uppval'] = (pricedata['RSI'] > 55) & (pricedata['RSI'] <= 100)
    pricedata['RSI_subval'] = (pricedata['RSI'] < 45) & (pricedata['RSI'] >= 0)

    pricedata['zone_upp_rsi'] = pricedata['RSI_uppval'].diff()
    pricedata['zone_sub_rsi'] = pricedata['RSI_subval'].diff()

    # ***********************************************************
    # * Estrategy
    # ***********************************************************

    pricedata['sell'] = pricedata.apply(lambda x: x.ema <= x.ema_slow and x.ema <=
                                        x.ema_res1 and x.ema <= x.ema_res2 and x.ema <= x.ema_res3, axis=1)
    pricedata['zone_sell'] = pricedata['sell'].diff()

    pricedata['buy'] = pricedata.apply(lambda x: x.ema >= x.ema_slow and x.ema >=
                                       x.ema_res1 and x.ema >= x.ema_res2 and x.ema >= x.ema_res3, axis=1)
    pricedata['zone_buy'] = pricedata['buy'].diff()

    # TRADING LOGIC BUY OPEN OPERATIONS
    rsiZoneUPP = ((pricedata['zone_upp_rsi'][len(pricedata) - 1] == True
                 or pricedata['zone_upp_rsi'][len(pricedata) - 2] == True 
                 or pricedata['zone_upp_rsi'][len(pricedata) - 3] == True ) 
                 and pricedata['RSI_uppval'][len(pricedata) - 1] == True )
    smaZoneUPP = (pricedata['zone_buy'][len(pricedata) - 1] and pricedata['buy'][len(pricedata) - 1])


    mediaVolumen = pricedata['tickqtySMA'][len(pricedata) - 1]


    print("Media Volumen:" + str(mediaVolumen))
    print("Media Volumen Actual:" + str(pricedata['tickqty'][len(pricedata) - 1]))

    pricedata['tickqtySMAFast'] = sma(pricedata['tickqty'], 10)
    pricedata['tickqtySMA'] = sma(pricedata['tickqty'], 100)

    VolumenTrend = False
    if pricedata['tickqtySMAFast'][len(pricedata) - 1] >= pricedata['tickqtySMA'][len(pricedata) - 2]: 
        VolumenTrend = True
    print("	VOLUMNE TREND  " + str(VolumenTrend))


    openBuy = False
    if rsiZoneUPP and smaZoneUPP:
        openBuy = False
    if rsiZoneUPP:
        print("	RSI ZONE UPP ")
    if smaZoneUPP:
        print("	SMA ZONE UPP ")


    if openBuy and VolumenTrend:
        print("	  BUY SIGNAL! ")
        if countOpenTrades("B") == 0:
            if countOpenTrades("S") > 0:
                exit("S")
            print("	  Opening Buy Trade...")
            enter("B")

    # TRADING LOGIC  BUY OPEN OPERATIONS
    rsiZoneSub = ((pricedata['zone_sub_rsi'][len(pricedata) - 1] == True
                    or pricedata['zone_sub_rsi'][len(pricedata) - 2] == True
                    or pricedata['zone_sub_rsi'][len(pricedata) - 3] == True)
                    and pricedata['RSI_subval'][len(pricedata) - 1] == True)
    smaZoneSub = (pricedata['zone_sell'][len(pricedata) - 1] and pricedata['sell'][len(pricedata) - 1])




    openSell = False
    if rsiZoneSub and smaZoneSub:
        openSell = True
        
    if rsiZoneSub:
        print("	RSI ZONE SUB ")
    if smaZoneSub:
        print("	SMA ZONE SUB ")

    if openSell and VolumenTrend:
        print("	  SELL SIGNAL!")
        if countOpenTrades("S") == 0:
            if countOpenTrades("B"):
                exit("B")
            print("	  Opening Sell Trade...")
            enter("S")

    #datatoprint = pricedata[['RSI', 'sell', 'zone_sell', 'RSI_uppval',
     #                        'zone_upp_rsi', 'buy', 'zone_buy', 'RSI_subval', 'zone_sub_rsi']]
    #datatoprint.to_csv(file)
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
