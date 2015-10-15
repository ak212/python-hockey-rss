# -*- coding: utf-8 -*-

from datetime import date, timedelta, datetime
import logging
import math
import os
import re
import sys
import threading
from time import localtime, strftime, mktime 
import urllib2

from bs4 import BeautifulSoup
import pymysql
from selenium import webdriver

import GameData
import markup
import retry_decorator


__author__ = "Aaron Koeppel"
__version__ = 2.0
__modified__ = '10/14/15'

team_abbrvs = ['ANA', 'ARI', 'BOS', 'BUF', 'CAR', 'CBJ', 'CGY', 'CHI', 'COL', 'DAL',
              'DET', 'EDM', 'FLA', 'LA', 'MIN', 'MTL', 'NSH', 'NJ', 'NYI', 'NYR',
              'OTT', 'PHI', 'PIT', 'SJ', 'STL', 'TB', 'TOR', 'VAN', 'WPG', 'WSH']

team_names = ['Ducks', 'Coyotes', 'Bruins', 'Sabres', 'Hurricanes', 'Blue Jackets',
              'Flames', 'Blackhawks', 'Avalanche', 'Stars', 'Red Wings', 'Oilers',
              'Panthers', 'Kings', 'Wild', 'Canadiens', 'Predators', 'Devils',
              'Islanders', 'Rangers', 'Senators', 'Flyers', 'Penguins', 'Sharks',
              'Blues', 'Lightning', 'Maple Leafs', 'Canucks', 'Jets', 'Capitals']

total_games = 0

logger = None
dbLastDate = None
driver = None

def initLogging():
   global logger
   file_name = str(date.today()) + '.log'
   
   script_dir = os.path.dirname(os.path.abspath(__file__))
   dest_dir = os.path.join(script_dir, "logs")
      
   try:
      os.makedirs(dest_dir)
   except OSError:
      pass
   
   path = os.path.join(dest_dir, file_name)
   
   logging.basicConfig(filename=path,
                       format='(%(threadName)-10s) %(message)s',
                       level=logging.DEBUG)
   logger = logging.getLogger(__name__)
   
def initDB():
   return pymysql.connect(host='localhost', port=3306, user='root', passwd=sys.argv[1], db='NHL')
   
def initDriver():
   global driver
   driver = webdriver.Firefox()
   
def insertGame(gameData, teamAb, teamName):
   connection = initDB()
   
   try:
      with connection.cursor() as cursor:
         sql = "INSERT INTO `GameData` VALUES (%s, %s, %s, %s, %s, %s, %s)"
         cursor.execute(sql, (gameData.id, gameData.link, gameData.headline,
                              gameData.date, gameData.result, teamAb, teamName))

      connection.commit()

   finally:
    connection.close()

def retrieveGames(teamAb):
   connection = initDB()
   result = None
   
   try:
      with connection.cursor() as cursor:
         sql = "SELECT * FROM `GameData` WHERE `team_ab`=%s"
         cursor.execute(sql, (teamAb))
         result = cursor.fetch()

   finally:
    connection.close()
    
   return result

def getTotalGames():
   connection = initDB()
   result = None
   
   try:
      with connection.cursor() as cursor:
         sql = "SELECT max(`id`) FROM `GameData`"
         cursor.execute(sql)
         result = cursor.fetchone()

   finally:
      connection.close()
   
   return result if result != None else 0

def getLastDate():
   connection = initDB()
   daysAgo = 365
   
   try:
      with connection.cursor() as cursor:
         sql = "SELECT game_date FROM `GameData` WHERE `id`=%s"
         cursor.execute(sql, (total_games))
         result = cursor.fetchone()
         
         currentDate = date.today()
       
         if result != None:
            for dateDB in result:
               # whatever the date string is
               formatDate = datetime.strptime(dateDB, "%Y%m%d").date()
               
               daysAgo = min((currentDate - formatDate).days, daysAgo)

   finally:
    connection.close()
    
    
   return currentDate - timedelta(days=daysAgo)

def pageResponse(link):
   '''Retrieve the source code of the page

   :param link: the link to the page that will be scraped
   :type link: string'''
   
   logger.debug("Requesting: " + link)
   response = urlopenWithRetry(link)
   page_source = response.read()
   
   return BeautifulSoup(page_source)

def threadJumpoff(team_ab, team_name):
   '''Intermediary function between the main function and the game extraction
   and xml generation

   :param team_ab: the team's abbreviated name
   :type team_ab: string
   :param team_name: the team's name
   :type team_name: string'''
   
   games = extractGameData(team_ab, team_name)
   games.sort(key=lambda x: x.date, reverse=True)
     
   markup.xmlMarkup(games, team_ab, team_name)

   logger.info(strftime("%d-%b-%Y %H:%M:%S ", localtime()) + team_name + 
               " completed with " + str(len(games)) + " games logged")

def extractGameData(team_ab, team_name):
   '''Extract the game data (date, headline, result) for each game the team 
   has played.

   :param team_ab: the team's abbreviated name
   :type team_ab: string
   :param team_name: the team's name
   :type team_name: string'''
   
   games = []
   link = "http://espn.go.com/nhl/team/schedule/_/name/" + team_ab
   soup = pageResponse(link)
   global total_games
   
   for div in soup.find_all(attrs={"class" : "score"}):
      recap_link_ending = str(div.find('a').get('href').encode('utf-8', 'ignore'))
      recap_link = "http://espn.go.com" + recap_link_ending
#      boxscore_link = "http://espn.go.com/nhl/boxscore?gameId=" + recap_link[36:]
      boxscore_link = recap_link
      
      recap_link_soup = pageResponse(recap_link)
      game_headline = getGameHeadline(recap_link_soup, recap_link)
      
      boxscore_link_soup = pageResponse(boxscore_link)
      game_date = getGameDate(boxscore_link_soup, boxscore_link)

#      if game_date != None:
#         date_of_game = datetime.strptime(game_date, "%d%m%Y").date()
#       
#      if (dbLastDate - date_of_game).days > 0:
      new_game = GameData.GameData(total_games, logger, recap_link, game_headline, game_date)
   
      total_games += 1
      
      new_game.charConvertLink()
      new_game.findWinner(team_name, boxscore_link_soup)
      new_game.modifyHeadline()
      #      new_game.print_game_data()
      insertGame(new_game, team_ab, team_name)
      games.append(new_game)
      
   return games

@retry_decorator.retry(urllib2.URLError, logger, tries=4, delay=3, backoff=2)
def urlopenWithRetry(link):
   return urllib2.urlopen(link)

def getGameHeadline(soup, link):
   '''Extract the headline from the page source.

   :param soup: the source file of the recap page
   :type soup: string
   :param link: the link to the page that will was scraped; passed in case of 
   error for logging
   :type link: string'''
   
#   driver = webdriver.Firefox()
#   driver.get(link)
#   headline = driver.title
#   driver.close()
#   return headline
   
   try:
      return soup.title.string
   except urllib2.HTTPError:
      logger.debug('There was an error with the request from: ' + link)
      
def getGameDate(soup, link):
   '''Extract the headline from the page source.

   :param soup: the source file of the recap page
   :type soup: string'''
   
#   driver = webdriver.Firefox()
#   driver.get(link)
#   date = driver.find_element_by_partial_link_text("Scores for").get_attribute("href")[39:]
#   driver.close()
#   return date

   try:
      base = soup.findAll('meta', {"name":'DC.date.issued'})
      date = base[0]['content'].encode('utf-8')[:10]
      return re.sub('-', '', date)
   except urllib2.HTTPError:
      logger.debug('There was an error with the request from: ' + link)
   except IndexError:
      logger.debug('Could not extract date from: ' + str(base))

      
def main():
   initLogging()
#   initDriver()
   total_games = getTotalGames()
   dbLastDate = getLastDate()
   
   
   start_time = localtime()
   logger.info("Start time: " + strftime("%d-%b-%Y %H:%M:%S ", start_time))
   
   threads = []
   for team_ab, team_name in zip(team_abbrvs, team_names):
      t = threading.Thread(name="Thread-" + team_ab,
                           target=threadJumpoff,
                           args=(team_ab, team_name))
      threads.append(t)

   # Start all threads
   [x.start() for x in threads]

   # Wait for all of them to finish
   [x.join() for x in threads]
   
   finish_time = localtime()
   logger.info("Finish time: " + strftime("%d-%b-%Y %H:%M:%S ", finish_time))
   logger.info("Total games: " + str(total_games))
   logger.info("Total time: " + 
               str(timedelta(seconds=mktime(finish_time) - mktime(start_time))))
   
if __name__ == '__main__':
   main()
