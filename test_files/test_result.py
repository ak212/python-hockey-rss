'''
Created on Oct 10, 2014

@author: Aaron
'''

import urllib2
from bs4 import BeautifulSoup
import sys
import re
import retry_decorator

def page_response(link):
   response = urllib2.urlopen(link)
   page_source = response.read()
   
   return BeautifulSoup(page_source)

def main():
   link = "http://scores.espn.go.com/nhl/recap?gameId=400564312"
   soup = page_response(link)
   
   for div in soup.find_all(attrs={"class" : "scoreboard-container"}):
      away_team = div.find_all(attrs={"class" : "away"})
      home_team = div.find_all(attrs={"class" : "home"})
      away_score = div.find_all(attrs={"class" : "awayScore"})
      home_score = div.find_all(attrs={"class" : "homeScore"})
      
      for aScore in away_score:
         print aScore.text
      
      for hScore in home_score:
         print type(hScore.text)      
               
main()