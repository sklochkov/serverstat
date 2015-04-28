#!/usr/bin/python2.6

import threading
import signal
import socket
import sys
import json
from collections import deque
import os
import re
import time

CPU_RE = re.compile("""^cpu\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)""")
MEMINFO_RE = re.compile("""^([a-zA-Z0-9\(\)_]+):\s+(\d+)\s.*$""")

# 10.625,3.625,85.750,0.0,0.0,0.0,0.0,0.0,1376.0,148.0,0.0,0.0,1226.0,3193.0
# user, system, idle, iowait, etc

PORT = 12012
PIDFILE = '/var/run/serverstat.pid'
p = None
sys_hz = os.sysconf(os.sysconf_names['SC_CLK_TCK'])

PARAMS = ['cpuuser', 'cpusystem', 'cpuidle', 'iowait', 'steal', 'guests', 'vmtotal', 'vmcache', 'vmfree', 'swaptotal', 'swapfree', 'dirty']

def dbl_fork():
	pid = os.fork()
	if pid:
		sys.exit(0)
	pid = os.fork()
	if pid:
                sys.exit(0)
	return True

def save_pidfile(pidfile):
	try:
		f = open(pidfile, 'w')
		f.write(str(os.getpid()))
		f.close()
	except:
		sys.exit(1)

def stop_handler(signum, frame):
	global p
	try:
		if p:
			p.kill()
	except:
		pass
	sys.exit(0)
	
signal.signal(signal.SIGTERM, stop_handler)
signal.signal(signal.SIGINT, stop_handler)

def format_results(q):
	res = {}
	l = len(q)
	if l == 0:
		return res
	for item in q:
		for param in PARAMS:
			if param in item:
				if param not in res:
					res[param] = item[param]
				else:
					res[param] += item[param]
	for param in PARAMS:
		if param in res:
			res[param] = res[param] / l
	return json.dumps(res)

def show_results(stats):
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(('0.0.0.0', PORT))
	s.listen(5)
	while True:
		try:
		        (conn, addr) = s.accept()
			res = format_results(stats)
			conn.send(res)
			conn.close()
		except Exception, ex:
			conn.send(str(ex))
			conn.close()

if __name__ == "__main__":
	dbl_fork()
	save_pidfile(PIDFILE)
	stats = deque(maxlen=60)
	#p = subprocess.Popen(['/usr/bin/dstat', '--noheaders', '--output', '/dev/stderr'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	t = threading.Thread(target=show_results, args=(stats,))
	t.daemon = True
	t.start()
	i = 0
	previous = {}
	while True:
		try:
			vmtotal = 0
			vmcache = 0
			vmfree = 0
			swaptotal = 0
			swapfree = 0
			dirty = 0
			f = open('/proc/stat')
			cpu_raw = f.readline()
			f.close()
			cpu_res = CPU_RE.match(cpu_raw)
			if not cpu_res:
				print "Invalid CPU regex"
			cpuuser = float(cpu_res.group(1))
			cpusystem = float(cpu_res.group(3))
			cpuidle = float(cpu_res.group(4))
			iowait = float(cpu_res.group(5))
			steal = float(cpu_res.group(8))
			guests = float(cpu_res.group(9))
			f = open('/proc/meminfo')
			for line in f:
				res = MEMINFO_RE.match(line)
				if not res:
					print "Invalid mem regex"
					continue
				if res.group(1) == "MemTotal":
					vmtotal = float(res.group(2))
				elif res.group(1) == "MemFree":
					vmfree = float(res.group(2))
				elif res.group(1) == "Cached":
					vmcache = float(res.group(2))
				elif res.group(1) == "SwapTotal":
					swaptotal = float(res.group(2))
				elif res.group(1) == "SwapFree":
					swapfree = float(res.group(2))
				elif res.group(1) == "Dirty":
					dirty = float(res.group(2))
			f.close()
			if not previous:
				previous['cpuuser'] = cpuuser
				previous['cpusystem'] = cpusystem
				previous['cpuidle'] = cpuidle
				previous['iowait'] = iowait
				previous['steal'] = steal
				previous['guests'] = guests
			else:
				stats.append({
					'cpuuser': cpuuser - previous['cpuuser'],
					'cpusystem': cpusystem - previous['cpusystem'],
					'cpuidle': cpuidle - previous['cpuidle'],
					'iowait': iowait - previous['iowait'],
					'steal': steal - previous['steal'],
					'guests': guests - previous['guests'],
					'vmtotal': vmtotal,
					'vmcache': vmcache,
					'vmfree': vmfree,
					'swaptotal': swaptotal,
					'swapfree': swapfree,
					'dirty': dirty})
		                previous['cpuuser'] = cpuuser
                		previous['cpusystem'] = cpusystem
		                previous['cpuidle'] = cpuidle
                		previous['iowait'] = iowait
		                previous['steal'] = steal
                		previous['guests'] = guests 
			time.sleep(1)
		except Exception, ex:
			print str(ex)
