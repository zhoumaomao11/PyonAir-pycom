#!/usr/bin/env python

from machine import RTC, Timer, SD, Pin
from PM_thread import pm_thread
from interrupt import ButtonPress
import _thread
import os
from LoggerFactory import LoggerFactory
from loggingpycom import INFO, WARNING, CRITICAL, DEBUG
from configuration import get_config
from EventScheduler import EventScheduler
import time

# Provisional globals
path = '/sd/'
sensor_name = 'PM1'
PM1_processing = path + sensor_name + '.csv.processing'
avg_interval = 15 * 60  # seconds


# Initialise the time
rtc = RTC()
rtc.init((2017, 2, 28, 10, 30, 0, 0, 0))  # TODO: if RTC has no time, set RTC time via Wifi and/or GPS
now = rtc.now()

# Mount SD card
sd = SD()
os.mount(sd, '/sd')

# Initialise LoggerFactory and loggers
logger_factory = LoggerFactory(level=DEBUG)
status_logger = logger_factory.create_status_logger('status_logger', filename='status_log.txt')
PM1_logger = logger_factory.create_sensor_logger(sensor_name)
status_logger.info('booted now')
status_logger.info('current working dir:' + str(os.getcwd()))

# Delete 'PM1.csv.processing' if it exists TODO: send the content over LoRa instead
if PM1_processing in os.listdir():
    status_logger.info(PM1_processing + 'already exists, removing it')
    os.remove(PM1_processing)

# Initialise interrupt for configuration over wifi
interrupt = ButtonPress(sd, logger=status_logger)
p = Pin("P14", mode=Pin.IN, pull=None)
p.callback(Pin.IRQ_FALLING | Pin.IRQ_RISING, interrupt.press_handler)

# Read configuration file
# settings = get_config(logger=status_logger)

# TODO: Process and send remaining data from previous boot

# Start 1st PM sensor thread with id: PM1
_thread.start_new_thread(pm_thread, (sd, sensor_name, PM1_logger))

# Calculate next event for average calculation
events = EventScheduler(avg_interval, rtc, logger=status_logger, sensor_name=sensor_name)

while True:
    # time.sleep(5)
    # flash_pm_averages(sensor_name, logger=status_logger)
    pass
