import fxcmpy
import datetime as dt
fxcmpy.__version__

#The server is demo by default. THe options below are also available for usage.
con = fxcmpy.fxcmpy(config_file='fxcm.cfg', server='demo')

start = dt.datetime(2022, 8, 1)
stop = dt.datetime(2022, 8, 5)

prices = con.get_candles('EUR/USD', period='D1', start=start, stop=stop)
print("Recived.." + str( dt.datetime.now())) 
print(prices)