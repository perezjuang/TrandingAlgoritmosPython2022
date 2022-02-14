import fxcmpy
import time
import datetime as dt
from datetime import datetime
from pyti.exponential_moving_average import exponential_moving_average as sma

token = '6729a4134f55808b3b57d80a92d480ddbb481837'
symbol = 'EUR/USD'
# Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8','D1', 'W1', or 'M1'.
timeframe = "m5"

fast_sma_periods = 100
slow_sma_periods = 1000

amount = 1
stop = -10
limit = 200

# Global Variables
pricedata = None
numberofcandles = 2000
con = None

# Monday, Tuesday, Wednesday, Thursday, and Friday
day_off_week_operate = list()
day_off_week_operate.append('Monday')
day_off_week_operate.append('Tuesday')
day_off_week_operate.append('Wednesday')
day_off_week_operate.append('Thursday')
day_off_week_operate.append('Friday')


def ReturnConection():
    global con
    valid_con = True
    while valid_con:
        try:
            #Check if day of week Valid
            print(datetime.today().strftime('%A'))
            if datetime.today().strftime('%A') in day_off_week_operate:
                print("Conecting....")
                con = fxcmpy.fxcmpy(access_token=token, log_level="error", log_file=None)
                print("Conected...")
                return con
            else:
                print("Wait a day in calendar to check again...")
                valid_con = False
                #2 Hours
                time.sleep(3600 * 2)
        except Exception as e:
            print("\n1.An exception occurred Obtaining Conection: " + symbol + " Exception: " + str(e))
            valid_con = True
            time.sleep(120)

con = ReturnConection()


# This function runs once at the beginning of the strategy to create price/indicator streams

def Prepare():
    global pricedata
    global con
    print("Requesting Initial Price Data...")
    pricedata = con.get_candles(symbol, period=timeframe, number=numberofcandles)
    print("Initial Price Data Received...")

# Get latest close bar prices and run Update() every close of bar per timeframe parameter

def StrategyHeartBeat():
    Update()
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


# Returns True when pricedata is properly updated

def getLatestPriceData():
    global pricedata
    global con
    print(str(dt.datetime.now()) + " Obtaining new prices Data ")
    try:
        if con.connection_status == "established":
            # Normal operation will update pricedata on first attempt
            new_pricedata = con.get_candles(symbol, period=timeframe, number=numberofcandles)
            if new_pricedata.index.values[len(new_pricedata.index.values) - 1] != pricedata.index.values[
                len(pricedata.index.values) - 1]:
                pricedata = new_pricedata
                print(str(dt.datetime.now()) + " Recived and Saved ")
                return True
            else:
                print("\n No updated prices found, trying again in 1 minute... \n")
                time.sleep(60)
                return True
        else:
            print("\n ******* Conexion not stablished ***** retry... in 10 minutes \n")
            time.sleep(600)
            con = ReturnConection()
            return True
    except Exception as e:
        print("\n1.An exception occurred Obtaining Prices and Conection: " + symbol + " Exception: " + str(e))
        time.sleep(300)
        con = ReturnConection()
        return True


# This function is run every time a candle closes
def Update():
    print(str(dt.datetime.now()) + " " + timeframe + " Bar Closed - Running Update Function...")

    # Calculate Indicators
    iFastSMA = sma(pricedata['bidclose'], fast_sma_periods)
    iSlowSMA = sma(pricedata['bidclose'], slow_sma_periods)

    # Print Price/Indicators
    print("Close Price: " + str(pricedata['bidclose'][len(pricedata) - 1]))
    print("Fast SMA: " + str(iFastSMA[len(iFastSMA) - 1]))
    print("Slow SMA: " + str(iSlowSMA[len(iSlowSMA) - 1]))

    # TRADING LOGIC
    if crossesOver(iFastSMA, iSlowSMA):
        print("   BUY SIGNAL!")
        if countOpenTrades("S") > 0:
            print("   Closing Sell Trade(s)...")
            exit("S")
        print("   Opening Buy Trade...")
        if countOpenTrades("B") == 0:
            enter("B")

    if crossesUnder(iFastSMA, iSlowSMA):
        print("   SELL SIGNAL!")
        if countOpenTrades("B") > 0:
            print("   Closing Buy Trade(s)...")
            exit("B")
        print("   Opening Sell Trade...")
        if countOpenTrades("S") == 0:
            enter("S")
    print(str(dt.datetime.now()) + " " + timeframe + " Update Function Completed.\n")
    print("\n")


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
        print("   Error Opening Trade.")
    else:
        print("   Trade Opened Successfully.")


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
                print("   Closing tradeID: " + position['tradeId'])
                try:
                    closetrade = con.close_trade(trade_id=position['tradeId'], amount=position['amountK'])
                except:
                    print("   Error Closing Trade.")
                else:
                    print("   Trade Closed Successfully.")


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
