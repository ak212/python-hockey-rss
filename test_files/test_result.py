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

def find_winner():
   link = "http://scores.espn.go.com/nhl/recap?gameId=400564461"
   soup = page_response(link)
   team_name = "Ducks"
   
   home_team = ""
   home_score = 0
   away_score = 0
   
   for div in soup.find_all(attrs={"class" : "matchup"}):
      for home in div.find_all(attrs={"class" : "team home"}):
         for name in home.find('a'):
            home_team = str(name)
         for score in home.find_all(attrs={"class" : "gp-homeScore"}):
            for val in score:
               home_score = int(val)
               
      for away in div.find_all(attrs={"class" : "team away"}):
         for score in away.find_all(attrs={"class" : "gp-awayScore"}):
            for val in score:
               away_score = int(val)
               

      
      home = home_team == team_name
      
      if home_score > away_score and home:
         return "W"
      elif home_score < away_score and home:
         return "L"
      elif home_score > away_score:
         return "L"
      elif home_score < away_score:
         return "W"
      else:
         return "error determining winner"
      
         
def main():
   result = find_winner()  
   print result
         
main()