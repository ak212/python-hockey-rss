'''
Created on Oct 16, 2014

@author: Aaron
'''
from datetime import timedelta
from time import localtime, sleep, mktime

start_time = localtime()
sleep(5)
finish_time = localtime()
print timedelta(seconds=mktime(finish_time)-mktime(start_time))