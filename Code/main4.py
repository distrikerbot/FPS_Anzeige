import psutil
import os
  
print(psutil.__version__)
print('RAM memory % used:', psutil.virtual_memory()[2])

load1, load5, load15 = psutil.getloadavg()
cpu_usage = (load15/os.cpu_count()) * 100
print("The CPU usage is : ", cpu_usage)
Distrikerbot — gestern um 16:24 Uhr