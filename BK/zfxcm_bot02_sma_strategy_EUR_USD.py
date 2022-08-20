#Robot Traiding
from ast import Return
import sys
import fxcmpy
import time
import datetime as dt
from datetime import datetime
from pyti.exponential_moving_average import exponential_moving_average as sma
from win10toast import ToastNotifier

token = 'd2bfd668f956b8e60892a2ba1eb24705ab8731ef'
symbol = 'USD/CAD'
# Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8','D1', 'W1', or 'M1'.
timeframe = "m5"

fast_sma_periods = 5
slow_sma_periods = 80

amount = 1
stop = -10
limit = 30

# Global Variables
pricedata = None
numberofcandles = 100
con = None

# Monday, Tuesday, Wednesday, Thursday, and Friday
day_off_week_operate = list()
day_off_week_operate.append('Monday')
day_off_week_operate.append('Tuesday')
day_off_week_operate.append('Wednesday')
day_off_week_operate.append('Thursday')
day_off_week_operate.append('Friday')

def Debug(msg = None):
  return (f"Debug {sys._getframe().f_back.f_lineno}:  {msg if msg is not None else ''}")


def Notifier(Notificacion = "Notification", NotificationBody = ""):
    toast = ToastNotifier()
    toast.show_toast(
        Notificacion,
        "NotificationBody",
        duration = 20,
        icon_path = "trading.ico",
        threaded = True,
    )

def ReturnConection():
    global con
    valid_con = True
    while valid_con:
        try:
            #Check if day of week Valid
            print( Debug(datetime.today().strftime('%A')) )
            if datetime.today().strftime('%A') in day_off_week_operate:
                print( Debug("Conecting....") )
                con = fxcmpy.fxcmpy(access_token=token,server='demo', log_level="error", log_file=None)
                print( Debug("Conected...") )
                return con
            else:
                print( Debug("Wait a day in calendar to check again...") )
                valid_con = False
                #2 Hours
                time.sleep(3600 * 2)
        except Exception as e:
            print( Debug("An exception occurred Obtaining Conection: " + symbol + " Exception: " + str(e)) )
            valid_con = True
            time.sleep(60)



# This function runs once at the beginning of the strategy to create price/indicator streams

def Prepare():
    global pricedata
    global con
    Notifier("   Start ")
    print( Debug("Requesting Initial Price Data...") )
    con = ReturnConection()
    pricedata = con.get_candles(symbol, period=timeframe, number=numberofcandles)
    print( Debug("Initial Price Data Received...") )

# Get latest close bar prices and run Update() every close of bar per timeframe parameter

def StrategyHeartBeat():
    while True:     
        if getLatestPriceData():
            Update()
            if timeframe == "m1":
                time.sleep(60 * 1)
            elif timeframe == "m5":
                time.sleep(60 * 5)
            elif timeframe == "m15":
                time.sleep(60 * 15)
            elif timeframe == "m30":
                time.sleep(60 * 30)
            else:
                time.sleep(60 * 60)

        


# Returns True when pricedata is properly updated
def getLatestPriceData():
    global pricedata
    global con
    print( Debug(str(dt.datetime.now()) + " Obtaining new prices Data ") )
    try:
        print( Debug( str( dt.datetime.now() ) + " " + str(con.connection_status) ) )
        if con.connection_status == "established":
            # Normal operation will update pricedata on first attempt
            new_pricedata = con.get_candles(symbol, period=timeframe, number=numberofcandles)
            if new_pricedata.index.values[len(new_pricedata.index.values) - 1] != pricedata.index.values[
                len(pricedata.index.values) - 1]:
                pricedata = new_pricedata
                print( Debug(str(dt.datetime.now()) + " Recived and Saved ") )
                return True
            else:
                print( Debug("\n No updated prices found, trying again in 1 minute... \n") )
                time.sleep(60)
                return False
        else:
            print( Debug("\n ******* Conexion not stablished ***** retry... in 5 minutes \n") )
            time.sleep(60 * 5)
            con = ReturnConection()
            return False
    except Exception as e:
        print( Debug("\n1.An exception occurred Obtaining Prices and Conection: " + symbol + " Exception: " + str(e)) )
        print( Debug("\n  retry... in 5 minutes \n") )
        Notifier("  Error ", str(e) )
        time.sleep(60 * 5)
        return False


# This function is run every time a candle closes
def Update():
    print( Debug(str(dt.datetime.now()) + " " + timeframe + " Bar Closed - Running Update Function...") )

    # Calculate Indicators
    iFastSMA = sma(pricedata['bidclose'], fast_sma_periods)
    iSlowSMA = sma(pricedata['bidclose'], slow_sma_periods)

    # print( Debug Price/Indicators
    print( Debug("Close Price: " + str(pricedata['bidclose'][len(pricedata) - 1])) )
    print( Debug("Fast SMA: " + str(iFastSMA[len(iFastSMA) - 1])) )
    print( Debug("Slow SMA: " + str(iSlowSMA[len(iSlowSMA) - 1])) )

    # TRADING LOGIC
    if crossesOver(iFastSMA, iSlowSMA):
        print( Debug("   BUY SIGNAL!") )
        Notifier("   BUY SIGNAL!","   BUY SIGNAL!")
        if countOpenTrades("S") > 0:
            print( Debug("   Closing Sell Trade(s)...") )
            exit("S")
        print( Debug("   Opening Buy Trade...") )
        if countOpenTrades("B") == 0:
            enter("B")

    if crossesUnder(iFastSMA, iSlowSMA):
        print( Debug("   SELL SIGNAL!") )
        Notifier("   SELL SIGNAL!","    SELL SIGNAL!")
        if countOpenTrades("B") > 0:
            print( Debug("   Closing Buy Trade(s)...") )
            exit("B")
        print( Debug("   Opening Sell Trade...") )
        if countOpenTrades("S") == 0:
            enter("S")
    print( Debug(str(dt.datetime.now()) + " " + timeframe + " Update Function Completed.\n") )

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


# This function places a market order in the direction BuySell, "B" = Buy, "S" = Sell, uses symbol, amount, stop, limit

def enter(BuySell):
    direction = True;
    if BuySell == "S":
        direction = False;
    try:
        opentrade = con.open_trade(symbol=symbol, is_buy=direction, amount=amount, time_in_force='GTC',
                                   order_type='AtMarket', is_in_pips=True, limit=limit, stop=stop)
    except:
        print( Debug("   Error Opening Trade.") )
    else:
        print( Debug("   Trade Opened Successfully.") )


# This function closes all positions that are in the direction BuySell, "B" = Close All Buy Positions,
# "S" = Close All Sell Positions, uses symbol

def exit(BuySell=None):
    openpositions = con.get_open_positions(kind='list')
    isbuy = True
    if BuySell == "S":
        isbuy = False
    for position in openpositions:
        if position['currency'] == symbol:
            if BuySell is None or position['isBuy'] == isbuy:
                print( Debug("   Closing tradeID: " + position['tradeId']) )
                try:
                    closetrade = con.close_trade(trade_id=position['tradeId'], amount=position['amountK'])
                except:
                    print( Debug("   Error Closing Trade.") )
                else:
                    print( Debug("   Trade Closed Successfully.") )


# Returns number of Open Positions for symbol in the direction BuySell, returns total number of both Buy and Sell positions if no direction is specified

def countOpenTrades(BuySell=None):
    openpositions = con.get_open_positions(kind='list')
    isbuy = True
    counter = 0
    if BuySell == "S":
        isbuy = False
    for position in openpositions:
        if position['currency'] == symbol:
            if BuySell is None or position['isBuy'] == isbuy:
                counter += 1
    return counter


Prepare()  # Initialize strategy
StrategyHeartBeat()  # Run strategy
