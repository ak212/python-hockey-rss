'''
Created on Oct 6, 2014

@author: Aaron
'''
import urllib2
from bs4 import BeautifulSoup
import sys
import re
from time import sleep

import markup
import retry_decorator
 
reload(sys)
sys.setdefaultencoding("utf-8") #@UndefinedVariable

team_abbrvs = ['ANA', 'ARI', 'BOS', 'BUF', 'CAR', 'CBJ', 'CGY', 'CHI', 'COL', 'DAL',
              'DET', 'EDM', 'FLA', 'LA', 'MIN', 'MTL', 'NAS', 'NJ', 'NYI', 'NYR', 
              'OTT', 'PHI', 'PIT', 'SJ', 'STL', 'TB', 'TOR', 'VAN', 'WPG', 'WSH']

team_names = ['Ducks', 'Coyotes', 'Bruins', 'Sabres', 'Hurricanes', 'Blue Jackets', 
              'Flames', 'Blackhawks', 'Avalanche', 'Stars','Red Wings', 'Oilers', 
              'Panthers', 'Kings', 'Wild', 'Canadiens', 'Predators', 'Devils', 
              'Islanders', 'Rangers', 'Senators', 'Flyers', 'Penguins', 'Sharks', 
              'Blues', 'Lightning', 'Maple Leafs', 'Canucks', 'Jets', 'Capitals']

class GameData(object):
   def __init__(self, link, headline, date):
      self.link = link
      self.headline = headline
      self.date = date
      
   def char_convert_link(self):
      self.link = re.sub('[&]', '&amp;', self.link)
      
   def print_game_data(self):
      print self.headline
      print self.link
      print self.date
      
   def list_data(self):
      return [self.headline, self.link, self.date]
   
def page_response(link):
   response = urlopen_with_retry(link)
   page_source = response.read()
   
   return BeautifulSoup(page_source)

def extract_game_data(team):
   games = []
   link = "http://espn.go.com/nhl/team/schedule/_/name/" + team
   soup = page_response(link)
   
   for div in soup.find_all(attrs={"class" : "score"}):
      complete_link = "http://espn.go.com" + str(div.find('a').get('href').encode('utf-8', 'ignore'))

      new_game = GameData(complete_link, get_game_headline(complete_link), get_game_date(complete_link))
      new_game.char_convert_link()
      games.append(new_game)
      
   return games

@retry_decorator.retry(urllib2.URLError, tries=4, delay=5, backoff=2)
def urlopen_with_retry(link):
   return urllib2.urlopen(link)

def get_game_headline(link):
   try:
      soup = page_response(link)
   
      for meta in soup.findAll('meta', {"property":'og:title'}):
         return meta.get('content')
   except urllib2.HTTPError:
      print 'There was an error with the request'
      
def get_game_date(link):
   soup = page_response(link)
   
   for div in soup.find_all(attrs={"class" : "scoreboard-strip-wrapper"}):
      #print div
      date_string = str(div.find('a').get('href').encode('utf-8', 'ignore'))
      #print date_string
      return date_string[21:]
      
def main():
   for team_ab, team_name in zip(team_abbrvs, team_names):
      games = extract_game_data(team_ab)
      games.sort(key=lambda x: x.date, reverse=True)
     
#      for game in games:
#         print game.list_data()
      markup.xml_markup(games, team_ab, team_name)
      
      print "Completed " + team_name
      
main()