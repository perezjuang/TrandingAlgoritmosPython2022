from multiprocessing.connection import wait
import time
import fxcmpy
import configparser



global con
config = configparser.ConfigParser()
config.read('RobotV5.ini')
#con = fxcmpy.fxcmpy(config_file='fxcm.cfg')
i = True
while i:
    print("Iniciando Con 1 ")
    try:
        con = fxcmpy.fxcmpy(server='demo',access_token='cfc00f60a0f97eb0d837adf1b109c11f327421e3', log_level="error", log_file="zfxcm.log")
        i = False
    except Exception as e:
        print(e)        
        i = True
    time.sleep(5)



