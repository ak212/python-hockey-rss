'''
Created on Sep 24, 2014

@author: Aaron Koeppel
'''

import urllib2
from bs4 import BeautifulSoup
import sys
import re

reload(sys)
sys.setdefaultencoding("utf-8") #@UndefinedVariable

class GameData(object):
   def __init__(self, link, headline):
      self.link = link
      self.headline = headline
      
   def char_convert_link(self, link):
      self.link = re.sub('[&]', '&amp;', self.link)

def extract_game_data():
   games = []
#   w = open("out.txt", 'w')
   response = urllib2.urlopen("http://espn.go.com/nhl/team/schedule/_/name/pit/pittsburgh-penguins")
   page_source = response.read()
   soup = BeautifulSoup(page_source)
   
   for div in soup.find_all(attrs={"class" : "score"}):
      complete_link = "http://espn.go.com" + str(div.find('a').get('href').encode('utf-8', 'ignore'))
#      print complete_link

      new_game = GameData(complete_link, get_game_headline(complete_link))
      new_game.char_convert_link(new_game.link)
      games.append(new_game)
      
   return games

def get_game_headline(link):
   response = urllib2.urlopen(link)
   page_source = response.read()
   soup = BeautifulSoup(page_source)
   
   for meta in soup.findAll('meta', {"property":'og:title'}):
      return meta.get('content')

def markup(games):
   xml = open("feed.xml", 'w')
   xml.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
   xml.write("<rss version='2.0'>\n")
   xml.write("<channel>\n")
   xml.write("<title>Penguins scores</title>\n")
   xml.write("<description>Latest Penguins scores</description>\n")
   xml.write("<link>http://espn.go.com/nhl/team/schedule/_/name/pit/pittsburgh-penguins</link>\n")
   
   for game in games:
      xml.write("<item>\n")
      xml.write("<title>%s</title>\n" % game.headline)
#      xml.write("<description></description>\n")
      xml.write("<link>%s</link>\n" % game.link)
      xml.write("</item>\n")
   xml.write("</channel>\n</rss>")
   xml.close()
      
def main():
   games = extract_game_data()
   games.reverse()
  
   for game in games:
      print game.link
      print game.headline
   markup(games)
         
main()