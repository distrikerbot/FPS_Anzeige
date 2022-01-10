import ctypes
import sys

import wmi
import time
import os
import subprocess

import win32gui
import win32process
import psutil


from ctypes import wintypes, byref



from threading import Timer

class Watchdog(Exception):
    def __init__(self, timeout, userHandler=None):  # timeout in seconds
        self.timeout = timeout
        self.handler = userHandler if userHandler is not None else self.defaultHandler
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()

    def reset(self):
        self.timer.cancel()
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()

    def stop(self):
        self.timer.cancel()

    def defaultHandler(self):
        raise self



stats = [{
	"Name": "GPU Core",
	"Type": "Temperature"
},	{
	"Name": "CPU Package",
	"Type": "Temperature"
},	{
	"Name": "CPU Total",
	"Type": "Load"
},	{
	"Name": "GPU Core",
	"Type": "Load"
},	{
	"Name": "Memory",
	"Type": "Load"
}]



w = wmi.WMI(namespace="root\OpenHardwareMonitor")

def get_stats():
	vals = []

	temperature_infos = w.Sensor()
	for sensor in temperature_infos:
		for s in stats:
			if(sensor.Name == s["Name"] and sensor.SensorType == s["Type"]):
				vals.append(sensor)


	#print("\033c")
	for v in vals:
		print(v.Name, v.SensorType, v.Value)


def get_active_window_name():
	hWnd = win32gui.GetForegroundWindow()
	_, pid = win32process.GetWindowThreadProcessId(hWnd)
	path = psutil.Process(pid).exe()
	name = os.path.basename(path)
	return name



proc = subprocess.Popen(["PresentMon-1.6.0-x64.exe", "-output_stdout", "-dont_restart_as_admin", "-qpc_time", "-stop_existing_session"] ,stdout=subprocess.PIPE)

clear = True

def resetClear():
	global clear
	# clear = True
	# print("Watchdog")

wd = Watchdog(0.01, resetClear)
while True:

	if clear:
		print("\n\033c\n")
		clear = False

	line = proc.stdout.readline()
	if not line:
		print(">>> not line")
		break

	line = str(line.rstrip())

	if("error" in line):
		pass
	else:
		# print(line)
		#print("\033c")
		active = get_active_window_name()
		if(active in line):
			spl = line.split(",")
			frametime = float(spl[11])
			fps = 1 / (frametime * (10**-3))
			print(active, round(fps), frametime)
			
		wd.reset()