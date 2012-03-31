import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string, sys, os
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
import HTMLParser


try:
	from sqlite3 import dbapi2 as sqlite
	print "Loading sqlite3 as DB engine"
except:
	from pysqlite2 import dbapi2 as sqlite
	print "Loading pysqlite2 as DB engine"

addon_id = 'plugin.video.irfree'
plugin = xbmcaddon.Addon(id=addon_id)

DB = os.path.join(xbmc.translatePath("special://database"), 'irfree.db')
BASE_URL = 'http://www.irfree.com'
net = Net()
addon = Addon('plugin.video.irfree', sys.argv)
autoPlay = True

if plugin.getSetting('autoPlay') == 'false':
        autoPlay = False
        

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
section = addon.queries.get('section', None)
query = addon.queries.get('query', None)
startPage = addon.queries.get('startPage', None)
numOfPages = addon.queries.get('numOfPages', None)
content = addon.queries.get('content', None)
listitem = addon.queries.get('listitem', None)


def GetTitles(url, startPage= '1', numOfPages= '1'): # Get Movie Titles
        print 'irfree get Movie Titles Menu %s' % url

        # handle paging
        pageUrl = url
        if int(startPage) > 1:
                pageUrl = url + 'page/' + startPage + '/'
        html = net.http_GET(pageUrl).content
        start = int(startPage)
        end = start + int(numOfPages)
        last = 2
        match  = re.findall('/page/[\d]+/">([\d]+)<', html)
        if len(match) > 0:
                last = match[len(match) -  1]
                last = int(last) + 1
        print str(start) + ' : ' + str(end) + ' : ' + str(last)
        for page in range( start, min(last, end)):
                if ( page != start):
                        pageUrl = url + 'page/' + str(page) + '/'
                        html = net.http_GET(pageUrl).content
                ListTitles(html)
       	if end < last:
                addon.add_directory({'mode': 'GetTitles', 'url': url, 'startPage': str(end), 'numOfPages': numOfPages}, {'title':  'Next..'})
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def ListTitles(html):
        print ' in ListTitles'
        match = re.compile('newsTitle"><a href="(.+?)">(.+?)<', re.DOTALL).findall(html)
        for url, title in match:
                addon.add_directory({'mode': 'GetLinks', 'url': url}, {'title':  title})


def GetLinks(url): # Get TV Links
        print 'In GetLinks'
        html = net.http_GET(url).content
        match = re.compile('href="(.+?)" rel="nofollow" target="_blank">[\s]*http').findall(html)
        listitem = GetMediaInfo(html)
        for url in match:
                host = GetDomain(url)
                print '*****************************' + host + ' : ' + url
                if urlresolver.HostedMediaFile(url= url):
                        if 'extabit.com' in url:
                                print 'Auto url is %s' % url
                                autoUrl = url
                        addon.add_directory({'mode': 'PlayVideo', 'url': url, 'listitem': listitem}, {'title':  host})
        if autoPlay:
                PlayVideo(autoUrl, listitem)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def PlayVideo(url, listitem):
        print 'in PlayVideo %s' % url
        stream_url = urlresolver.HostedMediaFile(url).resolve()
	xbmc.Player().play(stream_url, listitem)

def GetDomain(url):
        tmp = re.compile('//(.+?)/').findall(url)
        domain = 'Unknown'
        if len(tmp) > 0 :
            domain = tmp[0].replace('www.', '')
        return domain


def GetMediaInfo(html):
        listitem = xbmcgui.ListItem()
        match = re.search('og:title" content="(.+?) \((.+?)\)', html)
        if match:
                print match.group(1) + ' : ' + match.group(2)
                listitem.setInfo('video', {'Title': match.group(1), 'Year': int(match.group(2)) } )
        return listitem

def Categories(section):  #categories

        html = net.http_GET(BASE_URL).content
        match = re.compile('<li.+?href="/' + section + '(.+?)".+?<b>(.+?)<').findall(html)
        for cat, title in match:
                url = BASE_URL + '/' + section + cat
                addon.add_directory({'mode': 'GetTitles', 'url': url,
                                     'startPage': '1', 'numOfPages': '2'}, {'title':  title})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        

def MainMenu():    #homescreen
        addon.add_directory({'mode': 'Categories', 'section': 'movies'},  {'title':  'Movies'})
        addon.add_directory({'mode': 'Categories', 'section': 'tv-shows'},  {'title':  'TV Shows'})
        addon.add_directory({'mode': 'GetSearchQuery'},  {'title':  'Search'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def ListMovies(url):
        match = re.compile('href="(.+?)">(.+?)<').findall(content)
        for url, title in match:
                addon.add_directory({'mode': 'GetTitles', 'url': url, 'startPage': '1', 'numOfPages': '2'}, {'title':  title.encode('utf-8')})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def BrowseGenre(content):
        match = re.compile('href="(.+?)">(.+?)<').findall(content)
        for url, title in match:
                addon.add_directory({'mode': 'GetLinks', 'url': url, 'startPage': '1', 'numOfPages': '3'}, {'title':  title.encode('utf-8')})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
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
                Search( query)
	else:
                return

def Search(query):
        url = 'http://www.google.com/search?q=site:irfree.com ' + query
        url = url.replace(' ', '+')
        print url
        html = net.http_GET(url).content
        match = re.compile('<h3 class="r"><a href="(.+?)".+?onmousedown=".+?">(.+?)</a>').findall(html)
        for url, title in match:
                title = title.replace('<b>...</b>', '').replace('<em>', '').replace('</em>', '')
                addon.add_directory({'mode': 'GetLinks', 'url': url}, {'title':  title})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode == 'main': 
	MainMenu()
elif mode == 'BrowseGenre':
	BrowseGenre(content)
elif mode == 'GetTitles': 
	GetTitles(url, startPage, numOfPages)
elif mode == 'ListMovies': 
	ListMovies(url)
elif mode == 'GetLinks':
	GetLinks(url)
elif mode == 'GetSearchQuery':
	GetSearchQuery()
elif mode == 'Search':
	Search(query)
elif mode == 'Categories':
	Categories(section)
elif mode == 'ResolverSettings':
        urlresolver.display_settings()
elif mode == 'PlayVideo':
	PlayVideo(url, listitem)
