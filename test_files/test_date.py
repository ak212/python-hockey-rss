'''
Created on Oct 10, 2014

@author: Aaron
'''

import urllib2
from bs4 import BeautifulSoup

def page_response(link):
   response = urllib2.urlopen(link)
   page_source = response.read()
   
   return BeautifulSoup(page_source)

def main():
   link = "http://scores.espn.go.com/nhl/recap?gameId=400564312"
   soup = page_response(link)
   
   for div in soup.find_all(attrs={"class" : "scoreboard-strip-wrapper"}):
      date_string = str(div.find('a').get('href').encode('utf-8', 'ignore'))
      print date_string[21:]
   
main()