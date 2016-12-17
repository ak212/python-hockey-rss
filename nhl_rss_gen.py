# -*- coding: utf-8 -*-

from datetime import date, timedelta, datetime
import re
import sys
import threading
from time import localtime, mktime 
import urllib2

from bs4 import BeautifulSoup
import pymysql

import GameData
import log
import markup
import retry_decorator

__author__ = "Aaron Koeppel"
__version__ = 2.11
__modified__ = '10/17/2016'

teamAbbrvs = ['ANA', 'ARI', 'BOS', 'BUF', 'CAR', 'CBJ', 'CGY', 'CHI', 'COL', 'DAL',
              'DET', 'EDM', 'FLA', 'LA', 'MIN', 'MTL', 'NSH', 'NJ', 'NYI', 'NYR',
              'OTT', 'PHI', 'PIT', 'SJ', 'STL', 'TB', 'TOR', 'VAN', 'WPG', 'WSH']

teamNames = ['Ducks', 'Coyotes', 'Bruins', 'Sabres', 'Hurricanes', 'Blue Jackets',
              'Flames', 'Blackhawks', 'Avalanche', 'Stars', 'Red Wings', 'Oilers',
              'Panthers', 'Kings', 'Wild', 'Canadiens', 'Predators', 'Devils',
              'Islanders', 'Rangers', 'Senators', 'Flyers', 'Penguins', 'Sharks',
              'Blues', 'Lightning', 'Maple Leafs', 'Canucks', 'Jets', 'Capitals']

logger = log.setup_custom_logger('root')
dbLastDate = None
totalGames = None

seasonStart = "20160901"
   
def initDB():
   return pymysql.connect(host='localhost', port=3306, user='root', passwd=sys.argv[1], db='NHL_RSS')
   
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
   games = []
   logger.debug(connection)
   
   try:
#      logger.debug('About to get cursor')
      with connection.cursor() as cursor:
         sql = "SELECT * FROM `GameData` WHERE `team_ab`=%s"
         cursor.execute(sql, (teamAb))
#         logger.debug('Just used cursor')
         result = cursor.fetchall()
#         logger.debug('Fetched with cursor')

   finally:
      logger.debug('Trying to close connection')
      connection.close()
      logger.debug('Closed Connection with ' + len(result) + ' games')
    
   for game in result:
      games.append(GameData.GameData(game[0], game[1], game[2], game[3], game[4]))

   return games

def getTotalGames():
   global totalGames
   connection = initDB()
   result = None
   
   try:
      with connection.cursor() as cursor:
         sql = "SELECT max(id) FROM `GameData`"
         cursor.execute(sql)
         result = cursor.fetchone()

   finally:
      connection.close()
   
   if result[0] != None:
      totalGames = int(result[0]) + 1
   else:
      totalGames = 0

def getLastDate():
   global dbLastDate
   global totalGames
   
   connection = initDB()
   daysAgo = 365
   
   try:
      with connection.cursor() as cursor:
         sql = "SELECT game_date FROM `GameData` WHERE `id`=%s"
         cursor.execute(sql, (str(totalGames)))
         result = cursor.fetchone()
         
         currentDate = date.today()
       
         if result != None:
            for dateDB in result:
               # whatever the date string is
               formatDate = datetime.strptime(dateDB, "%Y%m%d").date()
               
               daysAgo = min((currentDate - formatDate).days, daysAgo)

   finally:
      connection.close()
    
    
   dbLastDate = currentDate - timedelta(days=daysAgo)

def pageResponse(link):
   '''Retrieve the source code of the page

   :param link: the link to the page that will be scraped
   :type link: string'''
   
   logger.debug("Requesting: " + link)
   response = urlopenWithRetry(link)
   pageSource = response.read()
   logger.debug("Read page: " + link)
   
   return BeautifulSoup(pageSource)

def teamExtractAndMarkup(teamAb, teamName):
   '''Intermediary function between the main function and the game extraction
   and xml generation

   :param teamAb: the team's abbreviated name
   :type teamAb: string
   :param teamName: the team's name
   :type teamName: string'''
   
   gamesInfo = extractGameData(teamAb, teamName)
   teamRecord = gamesInfo[0]
   games = gamesInfo[1]
   games.sort(key=lambda x: x.date, reverse=True)
   
   markup.xmlMarkup(games, teamAb, teamName, teamRecord)

   logger.info(teamName + " completed with " + str(len(games)) + " games logged")

def getTeamRecord(soup):
   return soup.find(class_="sub-title").text

def extractGameData(teamAb, teamName):
   '''Extract the game data (date, headline, result) for each game the team 
   has played.

   :param teamAb: the team's abbreviated name
   :type teamAb: string
   :param teamName: the team's name
   :type teamName: string'''
   
   global totalGames
   global logger
   
   games = retrieveGames(teamAb)
   logger.info("Found " + len(games) + " games for " + teamName)
   links = [game.link for game in games]
   schedLink = "http://espn.go.com/nhl/team/schedule/_/name/" + teamAb
   soup = pageResponse(schedLink)
   teamRecord = getTeamRecord(soup)
   
   for div in soup.find_all(attrs={"class" : "score"}):
      recapLink = re.sub('//www.', 'http://', str(div.find('a').get('href').encode('utf-8', 'ignore')))
      logger.info("Here's a recap link: " + recapLink)
      if "recap" in recapLink:
         if recapLink not in links:
            boxscoreLink = "http://espn.go.com/nhl/boxscore?gameId=" + recapLink[35:]
            
            recapLinkSoup = pageResponse(recapLink)
            gameHeadline = getGameHeadline(recapLinkSoup, recapLink)
            gameDate = getGameDate(recapLinkSoup, recapLink)
      
            if gameDate == "PRE":
               formattedDate = datetime.strptime(seasonStart, "%Y%m%d").date()
            elif gameDate != None:
               formattedDate = datetime.strptime(gameDate, "%Y%m%d").date()
            else:
               formattedDate = datetime.strptime(seasonStart, "%Y%m%d").date()
             
            formattedDate = formattedDate - timedelta(days=1)
             
            if (formattedDate - dbLastDate).days > 0:
               newGame = GameData.GameData(totalGames, recapLink, gameHeadline, re.sub('-', '', str(formattedDate)))
         
               totalGames += 1
               
               newGame.charConvertLink()
               boxscoreLinkSoup = pageResponse(boxscoreLink)
               newGame.findWinner(teamName, boxscoreLink, boxscoreLinkSoup)
               newGame.modifyHeadline()
               #      newGame.print_game_data()
               insertGame(newGame, teamAb, teamName)
               games.append(newGame)

         else:
            logger.debug("Already have game with link " + recapLink)
      
   return [teamRecord, games]

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
   
   try:
      return soup.title.string
   except urllib2.HTTPError:
      logger.debug('There was an error with the request from: ' + link)
      
def getGameDate(soup, link):
   '''Extract the headline from the page source.

   :param soup: the source file of the recap page
   :type soup: string
   :param link: the link to the page that will was scraped; passed in case of 
   error for logging
   :type link: string'''
   
   try:
      if "boxscore" in link:
         return "PRE"
      else:
         base = soup.findAll('meta', {"name":'DC.date.issued'})
         date = base[0]['content'].encode('utf-8')[:10]
         return re.sub('-', '', date)
   except urllib2.HTTPError:
      logger.debug('There was an error with the request from: ' + link)
   except IndexError:
      logger.debug('Could not extract date from: ' + str(base))

      
def main():
   global totalGames
   getTotalGames()
   dbLastDate = getLastDate()
   
   
   startTime = localtime()
   logger.info("START RUN")
   
   threads = []
   for teamAb, teamName in zip(teamAbbrvs, teamNames):
#      logger.debug('Making thread for: ' + teamName)
      t = threading.Thread(name="Thread-" + teamAb,
                           target=teamExtractAndMarkup,
                           args=(teamAb, teamName))
      threads.append(t)
      
#   logger.info('I have: ' + len(threads) + ' threads')

   # Start all threads
   [thread.start() for thread in threads]

   # Wait for all of them to finish
   [thread.join() for thread in threads]
   
   getTotalGames()
   finishTime = localtime()
   logger.info("FINISH RUN")
   logger.info("Total games: " + str(totalGames))
   logger.info("Total time: " + 
               str(timedelta(seconds=mktime(finishTime) - mktime(startTime))))
   
if __name__ == '__main__':
   main()
