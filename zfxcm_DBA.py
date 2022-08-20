from ast import Try
import fxcmpy
import time
import datetime as dt
from pyti.exponential_moving_average import exponential_moving_average as sma
from dbOperations.database import Database
import configparser
config = configparser.ConfigParser()
config.read('RobotV5.ini')


# Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8','D1', 'W1', or 'M1'.
time_frame_operations = config['timeframe']
timeframe = time_frame_operations['timeframe']

# Global Variables
pricedata = None
numberofcandles =  int( time_frame_operations['numberofcandles'] )
symbol = time_frame_operations['symbol']

con = fxcmpy.fxcmpy(config_file='fxcm.cfg')
# This function runs once at the beginning of the strategy to create price/indicator streams
db = Database()

firststar = True

# Get latest close bar prices and run Update() every close of bar per timeframe parameter

def StrategyHeartBeat():
    global pricedata
    print("Requesting Initial Price Data...")
    while True:
        currenttime = dt.datetime.now()
        if timeframe == "m1" and currenttime.second == 0 and getLatestPriceData():
            db.insertmany(pricedata,symbol,timeframe)
        elif timeframe == "m5" and currenttime.second == 0 and currenttime.minute % 5 == 0 and getLatestPriceData():
            db.insertmany(pricedata,symbol,timeframe)
        elif timeframe == "m15" and currenttime.second == 0 and currenttime.minute % 15 == 0 and getLatestPriceData():
            db.insertmany(pricedata,symbol,timeframe)
        elif timeframe == "m30" and currenttime.second == 0 and currenttime.minute % 30 == 0 and getLatestPriceData():
            db.insertmany(pricedata,symbol,timeframe)
        elif currenttime.second == 0 and currenttime.minute == 0 and getLatestPriceData():
            db.insertmany(pricedata,symbol,timeframe)            
        time.sleep(1)


# Returns True when pricedata is properly updated

def getLatestPriceData():
    global pricedata
    global firststar
    global con
    print("Requesting Price Data..." +  str(dt.datetime.now()) )
    # Normal operation will update pricedata on first attempt
    try:
            new_pricedata = con.get_candles(symbol, period=timeframe, number=numberofcandles)

            if firststar:
                pricedata = new_pricedata
                firststar = False
                db.insertmany(pricedata,symbol,timeframe)

            print("Recived.." + str( dt.datetime.now())) 
            if new_pricedata.index.values[len(new_pricedata.index.values) - 1] != pricedata.index.values[
                len(pricedata.index.values) - 1]:
                pricedata = new_pricedata
                return True

            # If data is not available on first attempt, try up to 3 times to update pricedata
            counter = 0
            while new_pricedata.index.values[len(new_pricedata.index.values) - 1] == pricedata.index.values[
                len(pricedata.index.values) - 1] and counter < 3:
                print("No updated prices found, trying again in 10 seconds...")
                counter += 1
                time.sleep(10)
                new_pricedata = con.get_candles(symbol, period=timeframe, number=numberofcandles)

            if new_pricedata.index.values[len(new_pricedata.index.values) - 1] != pricedata.index.values[
                len(pricedata.index.values) - 1]:
                pricedata = new_pricedata
                print("Price Data OK..." +  str(dt.datetime.now()) )
                return True
            else:
                print("Price Data Not Updated..." +  str(dt.datetime.now()) )
                return False
    except Exception as e:
        print(e)
        print("Restablising")
        try:
            con.close()
        except:
            print("Exception Clossing CON")

        con = fxcmpy.fxcmpy(config_file='fxcm.cfg')
        print("Restablised")
        return False
    

StrategyHeartBeat() 