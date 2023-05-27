import subprocess
import threading
import queue

fileNames = ["Real_Time_EUR_CAD.py",
             "Real_Time_EUR_JPY.py",
             "Real_Time_EUR_USD.py",
             "Real_Time_EUR_CAD.py",
             "Real_Time_GBP_CAD.py",
             "Real_Time_GBP_JPY.py",
             "Plotter_EUR_USD.py"]

q = queue.Queue()

def worker():
    while True:
        item = q.get()
        print(f'Working on {item}')
        subprocess.run(["python", item])
        print(f'Finished {item}')
        q.task_done()

# Turn-on the worker thread.
threading.Thread(target=worker, daemon=True).start()

# Send thirty task requests to the worker.
for item in fileNames:
    q.put(item)

# Block until all tasks are done.
q.join()
print('All work completed')


