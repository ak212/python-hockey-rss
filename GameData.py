'''
Created on Sep 19, 2015

@author: Aaron
'''
import re

class GameData(object):
   '''Class to represent a game played by a hockey team.

   :param link: html link to the game recap from ESPN.com
   :type link: string
   :param headline: the headline from the game recap
   :type headline: string
   :param date: the date the game was played
   :type date: string'''
   
   def __init__(self, total_games, logger, link, headline, date):
      self.id = total_games
      self.logger = logger
      self.link = link
      self.headline = headline
      self.date = date
      self.result = None
      
   def charConvertLink(self):
      '''Convert ampersands from the character '&' to the character encoding 
      '&amp;' to properly request html'''
      
      self.link = re.sub('[&]', '&amp;', self.link)
      
   def printGameData(self):
      '''Print data of the class'''
      
      print self.id, self.headline, self.link, self.date, self.result
      
   def listData(self):
      '''Return the data of the class as a list'''
      return [self.headline, self.link, self.date, self.result]
   
   def modifyHeadline(self):
      '''Change the headline to also include the game date and the result of
      the game'''
      
      headline = self.headline
      
      if self.date != None:
         if self.date[4] == "0":
            self.headline = "[" + self.date[5:6] + "/" + self.date[6:] + "] "
         else:
            self.headline = "[" + self.date[4:6] + "/" + self.date[6:] + "] "
         try:
            self.headline = self.headline + self.result + " - " + headline
         except TypeError:
            self.logger.debug("TypeError from: " + self.link)
            try:
               self.headline = self.headline + self.result + " - No Headline"
            except TypeError:
               self.headline = self.headline + " - " + headline
         
         
   def findWinner(self, team_name, soup):
      '''Find the winner of the hockey game through the game recap.
   
      :param team_name: the name of the hockey team; used to check if this team
      was the winner
      :type team_name: string
      :param soup: the source file of the recap page
      :type soup: string'''
      
      try:
         home_soup = soup.find(class_="top-col home")
         home_team = home_soup.find(class_="teamname").text.encode('utf-8').lstrip().rstrip()
         home_score = int(soup.find(class_="home-score").text)
         away_score = int(soup.find(class_="away-score").text)
                        
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
            self.logger.debug("Error determining winner from: " + self.link)
            result = ""
   
         self.result = result
      except AttributeError:
               self.logger.debug("Couldn't find in: " + str(home_soup))
