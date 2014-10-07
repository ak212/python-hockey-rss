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
   def __init__(self, link, headline):
      self.link = link
      self.headline = headline
      
   def char_convert_link(self, link):
      self.link = re.sub('[&]', '&amp;', self.link)

def extract_game_data(team):
   games = []
#   sleep(0.5)
   link = "http://espn.go.com/nhl/team/schedule/_/name/" + team
   response = urlopen_with_retry(link)
   page_source = response.read()
   soup = BeautifulSoup(page_source)
   
   for div in soup.find_all(attrs={"class" : "score"}):
      complete_link = "http://espn.go.com" + str(div.find('a').get('href').encode('utf-8', 'ignore'))
#      print complete_link

      new_game = GameData(complete_link, get_game_headline(complete_link))
      new_game.char_convert_link(new_game.link)
      games.append(new_game)
      
   return games

@retry_decorator.retry(urllib2.URLError, tries=4, delay=5, backoff=2)
def urlopen_with_retry(link):
   return urllib2.urlopen(link)

def get_game_headline(link):
#   print link
#   sleep(1)
   
   try:
      response = urlopen_with_retry(link)
      page_source = response.read()
      soup = BeautifulSoup(page_source)
   
      for meta in soup.findAll('meta', {"property":'og:title'}):
         return meta.get('content')
   except urllib2.HTTPError:
      print 'There was an error with the request'
      
def main():
   for team_ab, team_name in zip(team_abbrvs, team_names):
      games = extract_game_data(team_ab)
      games.reverse()
     
      for game in games:
         print game.link
         print game.headline
         
      markup.xml_markup(games, team_ab, team_name)
      
main()
