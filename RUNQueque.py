import subprocess
from threading import Thread

fileNames = ["Real_Time_EUR_CAD.py",
             "Real_Time_EUR_JPY.py",
             "Real_Time_EUR_USD.py",
             "Real_Time_GBP_CAD.py",
             "Real_Time_GBP_JPY.py"]

# Define a function for the thread
def print_time( threadName, delay):
   subprocess.run(["python", threadName])

if __name__ == "__main__":
    try:
        for item in fileNames:
            thread = Thread( target = print_time, args =(item, 2, ) )
            thread.start()

    except:
        print("Error: unable to start thread")

