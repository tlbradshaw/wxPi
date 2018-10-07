#!/usr/bin/python

# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import time
import sys
import datetime
import logging
from Adafruit_IO import *

__all__ = ['writetoMQTT', '__all__']

mqttLogger = logging.getLogger('__main__')

def connected(client):
	mqttLogger.info('Connected to Adafruit IO!')
	

#mqtt = MQTTClient('tlbradshaw','4551326023d44215bc73c6367ad1b8f0')
aio = Client('4551326023d44215bc73c6367ad1b8f0')

#mqtt.on_connect = connected

#mqtt.connect()
#mqtt.loop_background()


def writetoMQTT(data):
	mqttLogger.debug(data)
	try:
		if data['temperature'] != -99:
#		mqtt.publish('home-outside-temperature', data['temperature'])
#		mqtt.publish('home-temperature', data['temperature']) 
			aio.send('home-outside-temperature', round(data['temperature']*1.8 +32, 2))
			mqttLogger.debug('Message posted to MQTT.')
		if data['humidity'] != -99:
#		mqtt.publish('home-outside-humidity', data['humidity'])
			aio.send('home-outside-humidity',data['humidity'])
	except:
		pass
	try:
		if data['rainfall'] != -99:
			rainfall = round(data['rainfall']/25.4, 2)
			aio.send('home-rainfall', rainfall)
	except:
		pass
	try:
		if data['rainrate'] != -99:
			rainfall = round(data['rainrate']/25.4, 2)
			aio.send('home-rainrate', rainfall)
	except:
		pass
