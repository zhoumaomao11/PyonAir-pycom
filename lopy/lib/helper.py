# Helper functions
import time
from strings import file_name_temp, PM1, PM2, current_ext
from configuration import config
import os
import _thread

pm_current_lock = _thread.allocate_lock()
pm_processing_lock = _thread.allocate_lock()
pm_dump_lock = _thread.allocate_lock()
pm_tosend_lock = _thread.allocate_lock()


def seconds_to_first_event(rtc, interval_s):
    """
    Computes number of seconds (float) until the first sensor average reading
    :param rtc: real time clock object containing current time up to microsecond precision
    :param interval_s: interval between average readings
    :type interval_s: int
    :return:  number of seconds until first event
    """
    now = rtc.now()
    first_event_s = interval_s - (((now[4] * 60) + now[5] + (now[6]) / 1000000) % interval_s)
    hours = interval_s // 3600
    if hours >= 1:
        first_event_s += hours * 3600
    return first_event_s


def minutes_from_midnight():
    """

    :return: Number of seconds from midnight
    :rtype: int
    """
    t = time.gmtime()
    hours, minutes = t[3], t[4]
    return (hours * 60) + minutes


def mean_across_arrays(arrays):
    """
    Computes elementwise mean across arrays.
    E.g. for input [[1, 2, 4], [5, 3, 6]] returns [3, 2.5, 5]
    :param arrays: list of arrays of the same length
    :return: elementwise average across arrays
    """
    out_arr = []
    n_arrays = len(arrays)
    # Iterate through the elements in an array
    for i in range(len(arrays[0])):
        sm = 0
        # Iterate through all the arrays
        for array in arrays:
            sm += array[i]
        out_arr.append(sm/n_arrays)
    return out_arr


def check_data_ready():
    is_def = {PM1: False, PM2: False}

    if config[PM1]:
        if file_name_temp.format(PM1, current_ext)[4:] in os.listdir('/sd'):
            is_def[PM1] = True
    if config[PM2]:
        if file_name_temp.format(PM2, current_ext)[4:] in os.listdir('/sd'):
            is_def[PM2] = True

    return is_def