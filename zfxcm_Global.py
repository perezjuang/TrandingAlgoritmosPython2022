import fxcmpy
import time
import datetime as dt
from pyti.exponential_moving_average import exponential_moving_average as sma
from dbOperations.database import Database
import configparser
import zfxcm_PlotterStrategy as zplt
from threading import Thread

config = configparser.ConfigParser()
config.read('RobotV5.ini')
#con = fxcmpy.fxcmpy(config_file='fxcm.cfg')
con = fxcmpy.fxcmpy(server='demo',access_token='b429b38c119b86d2f004b89ac9ae786fd8d6f379', log_level="error", log_file=None)
