'''
Created on Oct 6, 2014

@author: Aaron
'''
import os

list = range(9)

print list

for num in list:
   file_name = str(num) + "_feed.xml"
   script_dir = os.path.dirname(os.path.abspath(__file__))
   dest_dir = os.path.join(script_dir, "test", str(num))
   try:
      os.makedirs(dest_dir)
   except OSError:
         pass # already exists\
   path = os.path.join(dest_dir, file_name)
   with open(path, 'w') as xml:
      xml.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
      xml.write("<rss version='2.0'>\n")
      xml.close()