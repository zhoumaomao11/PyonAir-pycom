"""
Tasks to be called by event scheduler
"""

import uos
from helper import mean_across_arrays, minutes_from_midnight
import _thread
from LoRa_thread import lora_thread
from configuration import config
import strings as s
from helper import pm_current_lock, pm_processing_lock, pm_dump_lock, pm_tosend_lock


def send_over_lora(logger, is_def, timeout):
    """
    Starts a thread that connects to LoRa and sends averages of the raw data
    :type logger: LoggerFactory object (status_logger)
    :param is_def: Stores which sensors are defined in the form "sensor_name" : True/False
    :type is_def: dict
    :param timeout: Timeout for LoRa to send over data seconds
    :type timeout: int
    """
    _thread.start_new_thread(lora_thread, ('LoRa', logger, is_def, timeout))


def flash_pm_averages(logger, is_def):
    """
    Gets averages for specific columns of defined sensor data, loads them into a line and appends it to the file which
    the LoRa thread sends data from.
    A sensor is defined if it is ticked in the configuration and has data to be sent (has a current.csv file).
    :type logger: LoggerFactory object (status_logger)
    :param is_def: Stores which sensors are defined in the form "sensor_name" : True/False
    :type is_def: dict
    """

    # Only calculate averages if PM1 or PM2 or both sensors are enabled and have gathered data
    if (is_def["PM1"] or is_def["PM2"]):

        logger.info("Calculating averages over {} minute interval".format(config["PM_interval"]))

        try:
            # Header of current file for plantower sensors
            header = s.headers_dict_v4["PMS5003"]

            if is_def["PM1"]:
                # Get averages for PM1 sensor
                PM1_avg_readings_str = get_averages(s.PM1_processing, s.PM1_current, s.PM1_dump, header)

            if is_def["PM2"]:
                # Get averages for PM2 sensor
                PM2_avg_readings_str = get_averages(s.PM2_processing, s.PM2_current, s.PM2_dump, header)

            # Append averages to the line to be sent over LoRa according to which sensors are defined.
            if (is_def["PM1"] and is_def["PM2"]):
                line_to_append = str(minutes_from_midnight()) + ',' + str(config["PM1_id"]) + ',' + ','.join(PM1_avg_readings_str) + ',' + str(config["PM2_id"]) + ',' + ','.join(PM2_avg_readings_str) + '\n'
            elif is_def["PM1"]:
                line_to_append = str(minutes_from_midnight()) + ',' + str(config["PM1_id"]) + ',' + ','.join(PM1_avg_readings_str) + '\n'
            elif is_def["PM2"]:
                line_to_append = str(minutes_from_midnight()) + ',' + str(config["PM2_id"]) + ',' + ','.join(PM2_avg_readings_str) + '\n'

            # Append lines to sensor_name.csv.tosend
            with open(s.lora_tosend, 'w') as f_tosend:  # TODO: change permission to 'a', hence make a queue for sending
                f_tosend.write(line_to_append)

        except Exception as e:
            logger.error(e)


def get_averages(processing, current, dump, header):
    """
    Calculates averages for specific columns of a sensor log data to be sent over LoRa.
    Renames current file to processing, calculates averages and returns them to flash_pm_averages to get saved to
    the tosend file, finally it appends raw data to the dump file and removes processing.
    :param processing: sensor processing file name
    :type processing: str
    :param current: sensor current file name
    :type current: str
    :param dump: sensor dump file name
    :type dump: str
    :param header: sensor current file headers
    :type header: dict
    :return: average readings of specific columns
    :rtype: str
    """

    # Remove sensor_name.csv.processing if it exists
    with pm_processing_lock:
        try:
            uos.remove(processing)  # TODO: instead of removing, find a better way to deal with this
        except Exception:
            pass

        # Rename sensor_name.csv.current to sensor_name.csv.processing
        try:
            uos.rename(current, processing)
        except Exception:
            pass

        with open(processing, 'r') as f:
            # read all lines from processing
            lines = f.readlines()
            lines_lst = []  # list of lists that store average sensor readings from specific columns
            for line in lines:
                stripped_line = line[:-1]  # strip \n
                stripped_line_lst = str(stripped_line).split(',')  # split string to list at comas
                named_line = dict(zip(header, stripped_line_lst))  # assign each value to its header
                sensor_reading = []
                sensor_reading.append(int(named_line["PM10"]))
                sensor_reading.append(int(named_line["PM25"]))
                # Append extra lines here for more readings - update version number and back-end to interpret data
                lines_lst.append(sensor_reading)

            # Compute averages from sensor_name.csv.processing
            avg_readings_str = [str(int(i)) for i in mean_across_arrays(lines_lst)]

            # Delete sensor_name.csv.processing
            try:
                uos.remove(processing)
            except Exception:
                pass

            # Append content of sensor_name.csv.processing into sensor_name.csv
            with pm_dump_lock:
                with open(dump, 'a') as f:
                    for line in lines:
                        f.write(line)

            return avg_readings_str