import threading as t
import time
import subprocess
import sys
import logging
import os
import signal

from math import ceil, floor
from flask import Flask, request
from collections import deque

app      = Flask(__name__)		
QUEUE    = deque()

log_file_path = str(os.getcwd() + '/log/generator_client.log')

logging.basicConfig(filename=log_file_path,level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger('generator_client')

def get_ncpus():
	return str(int(subprocess.Popen(['nproc'], stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0]))
	
def is_cpu_value_available():
	return bool(QUEUE)

def get_cpu_value():
   	return QUEUE.popleft()

def put_cpu_value(item):
	QUEUE.append(item)

def run_process(cpu_util, ncpus):
	logger.info('Running lookbusy process: ncpus=' + ncpus + ' cpu_util=' + cpu_util)
	return subprocess.Popen(['lookbusy', '--ncpus', ncpus, '--cpu-util', cpu_util])
	
def kill_process(pid):
	os.kill(int(pid), signal.SIGTERM)


@app.route('/level')
def cpu_level():
	
	cpu_util = str(int(floor(float(request.args.get('cpu_util')))))
	put_cpu_value(cpu_util)
	return "Ok"

class CPULoaderClient(t.Thread):

	def __init__(self, delay, ncpus):
		
		t.Thread.__init__(self)
		self.delay     = delay
		self.ncpus     = ncpus
		self.pid_list  = []
		self.process   = None

	def run(self):

		while True: 
			
			while not is_cpu_value_available():

				time.sleep(self.delay)
			
			cpu_util    = get_cpu_value()

			if self.process != None:
				self.process.terminate()
				logger.info('Lookbusy process terminated: pid=' + str(self.process.pid))
				
			self.process = run_process(cpu_util, self.ncpus)
						
if __name__ == '__main__':
	
	ncpus	= get_ncpus()
	delay	= int(sys.argv[1])
	
	cpu_loader = CPULoaderClient(delay, ncpus)
	cpu_loader.start()

	app.run(host='0.0.0.0', port=5555)