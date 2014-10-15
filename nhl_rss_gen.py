# -*- coding: utf-8 -*-

'''
Created on Oct 6, 2014

@author: Aaron
'''
import urllib2
from bs4 import BeautifulSoup
import re
import logging
from datetime import date
from time import localtime, strftime

import markup
import retry_decorator

team_abbrvs = ['ANA', 'ARI', 'BOS', 'BUF', 'CAR', 'CBJ', 'CGY', 'CHI', 'COL', 'DAL',
              'DET', 'EDM', 'FLA', 'LA', 'MIN', 'MTL', 'NSH', 'NJ', 'NYI', 'NYR', 
              'OTT', 'PHI', 'PIT', 'SJ', 'STL', 'TB', 'TOR', 'VAN', 'WPG', 'WSH']

team_names = ['Ducks', 'Coyotes', 'Bruins', 'Sabres', 'Hurricanes', 'Blue Jackets', 
              'Flames', 'Blackhawks', 'Avalanche', 'Stars','Red Wings', 'Oilers', 
              'Panthers', 'Kings', 'Wild', 'Canadiens', 'Predators', 'Devils', 
              'Islanders', 'Rangers', 'Senators', 'Flyers', 'Penguins', 'Sharks', 
              'Blues', 'Lightning', 'Maple Leafs', 'Canucks', 'Jets', 'Capitals']

file_name = str(date.today()) + '.log'

logging.basicConfig(filename=file_name,
                    level=logging.DEBUG)

class GameData(object):
   def __init__(self, link, headline, date):
      self.link = link
      self.headline = headline
      self.date = date
      self.result = None
      
   def char_convert_link(self):
      self.link = re.sub('[&]', '&amp;', self.link)
      
   def print_game_data(self):
      print self.headline, self.link, self.date, self.result
      
   def list_data(self):
      return [self.headline, self.link, self.date, self.result]
   
   def modify_headline(self):
      headline = self.headline
      
      if self.date[4] == "0":
         self.headline = "[" + self.date[5:6] + "/" + self.date[6:] + "] "
      else:
         self.headline = "[" + self.date[4:6] + "/" + self.date[6:] + "] "
      try:
         self.headline = self.headline + self.result + " - " + headline
      except TypeError:
         logging.debug("TypeError from: " + self.headline)
         self.headline = self.headline + self.result + " No Headline"
         
   def find_winner(self, team_name, soup, link):
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
            result = "W"
         elif home_score < away_score and home:
            result = "L"
         elif home_score > away_score:
            result = "L"
         elif home_score < away_score:
            result = "W"
         else:
            logging.debug("Error determining winner from: " + link)
            result = ""

      self.result = result
   
def page_response(link):
   response = urlopen_with_retry(link)
   page_source = response.read()
   
   return BeautifulSoup(page_source)

def extract_game_data(team_ab, team_name):
   games = []
   link = "http://espn.go.com/nhl/team/schedule/_/name/" + team_ab
   soup = page_response(link)
   
   for div in soup.find_all(attrs={"class" : "score"}):
      complete_link = "http://espn.go.com" + str(div.find('a').get('href').encode('utf-8', 'ignore'))

      complete_link_soup = page_response(complete_link)
      game_headline = get_game_headline(complete_link_soup, complete_link)
      game_date = get_game_date(complete_link_soup)

      new_game = GameData(complete_link, game_headline, game_date)
      
      new_game.char_convert_link()
      new_game.find_winner(team_name, complete_link_soup, complete_link)
      new_game.modify_headline()
      
      games.append(new_game)
      
   return games

@retry_decorator.retry(urllib2.URLError, tries=4, delay=5, backoff=2)
def urlopen_with_retry(link):
   return urllib2.urlopen(link)

def get_game_headline(soup, link):
   try:
      for meta in soup.findAll('meta', {"property":'og:title'}):
         return meta.get('content')
   except urllib2.HTTPError:
      logging.debug('There was an error with the request from: ' + link)
      
def get_game_date(soup):
   for div in soup.find_all(attrs={"class" : "scoreboard-strip-wrapper"}):
      date_string = str(div.find('a').get('href').encode('utf-8', 'ignore'))

      return date_string[21:]
      
def main():
   for team_ab, team_name in zip(team_abbrvs, team_names):
      games = extract_game_data(team_ab, team_name)
      games.sort(key=lambda x: x.date, reverse=True)
     
      markup.xml_markup(games, team_ab, team_name)

      logging.info(str(len(games)) + " logged for " + team_name)
      logging.info(strftime("%d-%b-%Y %H:%M:%S ", localtime()) + team_name + " completed")
      
main()