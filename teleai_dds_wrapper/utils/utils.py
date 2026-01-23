import os
import time

def get_nano():
    return time.clock_gettime_ns(time.CLOCK_REALTIME)

def nano_sleep(ns):
    os.clock_nanosleep(time.CLOCK_MONOTONIC, 0, ns)