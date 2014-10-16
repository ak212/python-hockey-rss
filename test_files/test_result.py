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
   
   matchup = soup.find(class_="matchup")
   home = matchup.find(class_="team home")
   home_team = str(home.find('a').text)
   home_score = int(home.find(class_="gp-homeScore").text)
   away_score = int(matchup.find(class_="team away").find(class_="gp-awayScore").text)
      
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