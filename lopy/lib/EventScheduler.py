import machine
from machine import RTC, Timer
from tasks import flash_pm_averages, send_over_lora
from helper import seconds_to_first_event, check_data_ready
from configuration import config


class EventScheduler:
    def __init__(self, rtc, logger):

        #  Arguments
        self.interval_s = int(config["PM_interval"])*60
        self.rtc = rtc
        self.logger = logger

        #  Attributes
        self.s_to_next_lora = None
        self.first_alarm = None
        self.periodic_alarm = None
        self.random_alarm = None
        self.is_def = None

        #  Start scheduling events
        self.set_event_queue()

    #  Calculates time (s) until the first event, and sets up an alarm
    def set_event_queue(self):
        first_event_s = seconds_to_first_event(self.rtc, self.interval_s)
        self.first_alarm = Timer.Alarm(self.first_event, s=first_event_s, periodic=False)

    def first_event(self, arg):
        #  set up periodic alarm with specified interval to calculate averages
        self.periodic_alarm = Timer.Alarm(self.periodic_event, s=self.interval_s, periodic=True)
        self.periodic_event(arg)

    def periodic_event(self, arg):
        #  Check which sensors are turned on and which ones have data to be sent over
        self.is_def = check_data_ready()
        #  flash averages of data to sd card at the end of the interval
        flash_pm_averages(logger=self.logger, is_def=self.is_def)
        #  get random number of seconds within interval
        self.s_to_next_lora = int(machine.rng() / (2**24) * self.interval_s)
        #  set up an alarm with random delay to send data over LoRa
        self.random_alarm = Timer.Alarm(self.random_event, s=self.s_to_next_lora, periodic=False)

    def random_event(self, arg):
        send_over_lora(logger=self.logger, is_def=self.is_def, timeout=60)