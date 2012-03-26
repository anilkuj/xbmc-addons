import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string, sys, os
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net

try:
	from sqlite3 import dbapi2 as sqlite
	print "Loading sqlite3 as DB engine"
except:
	from pysqlite2 import dbapi2 as sqlite
	print "Loading pysqlite2 as DB engine"


DB = os.path.join(xbmc.translatePath("special://database"), 'tamilkey.db')
BASE_URL = 'http://www.tamilkey.org'
net = Net()
addon = Addon('plugin.video.tamilkey', sys.argv)

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
content = addon.queries.get('content', None)
query = addon.queries.get('query', None)
startPage = addon.queries.get('startPage', None)
numOfPages = addon.queries.get('numOfPages', None)


def GetTitles(url): # Get Movie Titles
        print 'tamilkey get Movie Titles Menu %s' % url
        html = net.http_GET(url).content
        match = re.search('class="azindex"', html)
        html = html[match.end():]
        match = re.search('azlinkspacer', html)
        html = html[:match.start()]
        
        match = re.compile('<li><a href="(.+?)".+?head">(.+?)<').findall(html)
        for url, name in match:
            addon.add_directory({'mode': 'GetLinks', 'url': BASE_URL + url}, {'title':  name})
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetLinks(url): # Get TV Links
        print 'In GetLinks %s' % url
        html = net.http_GET(url).content
        regex_list = ['embed src="(.+?)"', 'iframe.+?src="(.+?)" ]
        for regex in regex_list:
            match = re.compile(regex).findall(html)
            for url in match:
                    print 'in for loop: %s' % url
                    host = GetDomain(url)
                    if urlresolver.HostedMediaFile(host=host, media_id='xxx'):
                            addon.add_directory({'mode': 'PlayVideo', 'url': url}, {'title':  host})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def PlayVideo(url):
        print 'in PlayVideo %s' % url
        stream_url = urlresolver.HostedMediaFile(url).resolve()
	xbmc.Player().play(stream_url)

def GetDomain(url):
        tmp = re.compile('//(.+?)/').findall(url)
        domain = 'Unknown'
        if len(tmp) > 0 :
            domain = tmp[0].replace('www.', '')
        return domain


def MainMenu():  #homescreen

        html = net.http_GET(BASE_URL).content
        match = re.search("<ul class='children'>", html)
        html = html[match.end():]
        match = re.search('</ul>', html)
        html = html[:match.start()]
        #addon.add_directory({'mode': 'GetTitles', 'url': 'http://tamilkey.org/category/watch-tamil-movies-online/watch-latest-tamil-movies-online/watch-tamil-movie-latest-vcd-online'}, {'title':  '2012 VCD')})
        #addon.add_directory({'mode': 'GetTitles', 'url': 'http://tamilkey.org/category/watch-tamil-movies-online/watch-latest-tamil-movies-online/watch-tamil-latest-movies-dvd'}, {'title':  '2012 DVD')})
        match = re.compile('href="(.+?)">(.+?)<', , re.DOTALL | re.MULTILINE).findall(html)
        for url, title in match:
            addon.add_directory({'mode': 'GetTitles', 'url': url}, {'title':  title.replace('Tamil Movie ', '')})
        addon.add_directory({'mode': 'GetSearchQuery'},,  {'title':  'Search'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetSearchQuery():
	last_search = addon.load_data('search')
	if not last_search: last_search = ''
	keyboard = xbmc.Keyboard()
        keyboard.setHeading('Search TV Shows')
	keyboard.setDefault(last_search)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
                query = keyboard.getText()
                addon.save_data('search',query)
                Search(query)
	else:
                return

def Search(query):
        url = BASE_URL + '/?s='  + query
        html = net.http_GET(url).content
        results_start = re.search('series-found', html)
        html = html[results_start.end():]
        results_end = re.search('</a></li></ul></div></div>', html)
        html = html[:results_end.start()]
        print html
        match = re.compile('href="(.+?)".+?>(.+?)<').findall(html)
        for url, title in match:
                if '/series/' in url:
                        addon.add_directory({'mode': 'GetSeasons', 'url': url}, {'title':  title})
                else:
                        addon.add_directory({'mode': 'GetLinks', 'url': url}, {'title':  ShrinkTitle(title)})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


if mode == 'main': 
	MainMenu()
elif mode == 'BrowseGenre':
	BrowseGenre(content)
elif mode == 'GetTitles': 
	GetTitles(url, startPage, numOfPages)
elif mode == 'ListMovies': 
	ListMovies(content)
elif mode == 'GetLinks':
	GetLinks(url)
elif mode == 'GetSearchQuery':
	GetSearchQuery()
elif mode == 'Search':
	Search(query)

