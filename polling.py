# -*- coding: utf-8 -*

"""
Module for polling the various sensors.
"""

import time
import logging
import threading
import traceback
import pprint
try:
	import cStringIO as StringIO
except ImportError:
	import StringIO
from datetime import datetime, timedelta

from decoder import read433
from parser import parsePacketStream
from utils import computeDewPoint, computeSeaLevelPressure, wuUploader

from sensors.bmpBackend import BMP085

__version__ = "0.1"
__all__ = ["PollingProcessor", "__version__", "__all__"]


# Logger instance
pollLogger = logging.getLogger('__main__')


class PollingProcessor(threading.Thread):
	"""
	Class responsible to running the various zones according to the schedule.
	"""

	def __init__(self, config, db, leds, buildState=False, loopsForState=1, sensorData={}):
		threading.Thread.__init__(self)
		self.config = config
		self.db = db
		self.leds = leds
		self.buildState = buildState
		self.loopsForState = loopsForState
		self.sensorData = sensorData
		
		self.thread = None
		self.alive = threading.Event()
		
	def start(self):
		if self.thread is not None:
			self.cancel()
        	       
		self.thread = threading.Thread(target=self.run, name='poller')
		self.thread.setDaemon(1)
		self.alive.set()
		self.thread.start()
		
		pollLogger.info('Started the PollingProcessor background thread')
		
	def cancel(self):
		if self.thread is not None:
			self.alive.clear()          # clear alive event for thread
			self.thread.join()
			
		pollLogger.info('Stopped the PollingProcessor background thread')
		
	def run(self):
		tLastUpdate = 0.0
		sensorData = self.sensorData
		
		while self.alive.isSet():
			# pollLogger.debug('Getting the time')
			## Begin the loop
			t0 = time.time()
			pollLogger.debug('Initial time: ' +str(t0))
			
			## Load in the current configuration
			wuID = self.config.get('Account', 'id')
			wuPW = self.config.get('Account', 'password')
			
			radioPin = self.config.getint('Station', 'radiopin')
			duration = self.config.getfloat('Station', 'duration')
			elevation = self.config.getfloat('Station', 'elevation')
			enableBMP085 = self.config.getbool('Station', 'enablebmp085')
			includeIndoor = self.config.getbool('Station', 'includeindoor')
			
			## Read from the 433 MHz radio
			for i in xrange(self.loopsForState):
				self.leds['red'].on()
				tData = time.time() + int(round(duration-5))/2.0
				pollLogger.debug('Listen for packets for: ' + str(int(round(duration-5))))
				try:
					packets = read433(radioPin, int(round(duration-5)))
				except:
					pollLogger.debug('read433 error ')
				pollLogger.debug('Packets: ' + pprint.PrettyPrinter(indent=4).pformat(packets) + str(len(packets)))
				## ispackets = false	
				## if packets is not None:
				##	ispackets = true
			
				##  pollLogger.debug('Packets null? ' + str(ispackets))

				self.leds['red'].off()
				
				## Process the received packets and update the internal state
				self.leds['yellow'].on()
				sensorData = parsePacketStream(packets, elevation=elevation, 
												inputDataDict=sensorData)
				pollLogger.debug(sensorData)
			
				self.leds['yellow'].off()
				
				# Poll the BMP085/180 - if needed
				if enableBMP085:
					self.leds['red'].on()
					ps = BMP085(address=0x77, mode=3)
					pressure = ps.readPressure() / 100.0
					temperature = ps.readTemperature()
					self.leds['red'].off()
			
					self.leds['yellow'].on()
					sensorData['pressure'] =  pressure
					sensorData['pressure'] = computeSeaLevelPressure(sensorData['pressure'], elevation)
					if 'indoorHumidity' in sensorData.keys():
						sensorData['indoorTemperature'] = ps.readTemperature()
						sensorData['indoorDewpoint'] = computeDewPoint(sensorData['indoorTemperature'], sensorData['indoorHumidity'])
					self.leds['yellow'].off()
					
			## Have we built up the state?
			if self.buildState:
				self.loopsForState = 1
				
			## Check if there is anything to update in the archive
			self.leds['yellow'].on()
			if tData != tLastUpdate:
                                if len(packets) > 0:
                                    self.db.writeData(tData, sensorData)
                                    pollLogger.info('Saving current state to archive')
                                else:
                                    pollLogger.debug('No data to save, so archiving skipped')
			else:
				pollLogger.warning('Data timestamp has not changed since last poll, archiving skipped')
			self.leds['yellow'].off()

			pollLogger.debug('Attempting to add to WUnderground')
			
			# pollLogger.debug('This shouldnt get printed')
			## Post the results to WUnderground
			if tData != tLastUpdate:
				uploadStatus = wuUploader(wuID, wuPW, tData, sensorData, archive=self.db, includeIndoor=includeIndoor)
				
				# uploadStatus = true
				# pollLogger.debug('Skipping the WU upload')

				if uploadStatus:
					tLastUpdate = 1.0*tData
					
					pollLogger.info('Posted data to WUnderground')
					self.leds['green'].blink()
					time.sleep(3)
					self.leds['green'].blink()
				else:
					tLastUpdate = 1.0*tData
					pollLogger.error('Failed to post data to WUnderground')
					self.leds['red'].blink()
					time.sleep(3)
					self.leds['red'].blink()
					
			else:
				pollLogger.warning('Data timestamp has not changed since last poll, archiving skipped')

				
			pollLogger.debug('Attempting to sleep')
			## Done
			t1 = time.time()
			tSleep = duration - (t1-t0)
			##pollLogger.debug('Times: t1, t0, tSleep, duration: ' + str(t1) + ', ' + str(t0) + ', ' + str(tSleep) + ', ' + str(duration))
			## tSleep = tSleep if tSleep > 0 else 0
			tSleep = 5
			pollLogger.debug('Going to sleep for ' + str(tSleep) + ' seconds')
			
			## Sleep
			time.sleep(tSleep)
			
