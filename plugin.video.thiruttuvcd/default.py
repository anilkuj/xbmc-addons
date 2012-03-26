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

plugin = xbmcaddon.Addon(id=re.compile("plugin://(.+?)/").findall(sys.argv[0])[0])
DB = os.path.join(xbmc.translatePath("special://database"), 'thiruttuvcd.db')
BASE_URL = 'http://www.thiruttuvcd.com'
net = Net()
addon = Addon('plugin.video.thiruttuvcd', sys.argv)

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
content = addon.queries.get('content', None)
query = addon.queries.get('query', None)
listitem = addon.queries.get('listitem', None)
startPage = addon.queries.get('startPage', None)
numOfPages = addon.queries.get('numOfPages', None)


def GetTitles(url, startPage= '1', numOfPages= '1'): # Get Movie Titles
        print 'thiruttuvcd get Movie Titles Menu %s' % url

        # handle paging
        pageUrl = url
        if startPage > '1':
                pageUrl = url + 'page/' + startPage + '/'
        html = net.http_GET(pageUrl).content
        start = int(startPage)
        end = start + int(numOfPages)
        last = 2
        match  = re.search("page/([\d]+)/' class='last", html)
        if match:
                last = int(match.group(1)) + 1
        #print str(start) + ' : ' + str(end) + ' : ' + str(last)
        for page in range( start, min(last, end)):
                if ( page != start):
                        pageUrl = url + 'page/' + str(page)  + '/'
                        html = net.http_GET(pageUrl).content
                #print pageUrl
                match = re.compile('class="boxtitle".+?href="(.+?)".+?title="(.+?)[,"].+?src="(.+?)"', re.DOTALL | re.MULTILINE).findall(html)
                for movieUrl, title, img in match:
                        title = HTMLParser.HTMLParser().unescape(title)
                        addon.add_directory({'mode': 'GetLinks', 'url': movieUrl}, {'title':  title}, img= img)
        if end < last:
                addon.add_directory({'mode': 'GetTitles', 'url': url, 'startPage': str(end), 'numOfPages': numOfPages}, {'title':  'Next..'})
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetLinks(url): # Get TV Links
        print 'In GetLinks %s' % url
        html = net.http_GET(url).content
        match = re.compile('<iframe.+?src="(.+?)"').findall(html)
        #listitem = GetMediaInfo(html)
        for url in match:
                host = GetDomain(url)
                if urlresolver.HostedMediaFile(host=host, media_id='xxx'):
                        addon.add_directory({'mode': 'PlayVideo', 'url': url, 'listitem': listitem}, {'title':  host})
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
        match = re.search('og:title" content="(.+?) \(([\d]+)\)', html)
        if match:
                listitem.setInfo('video', {'Title': match.group(1), 'Year': int(match.group(2)) } )
        return listitem


def MainMenu():  #homescreen
        html = net.http_GET(BASE_URL).content
        match = re.compile("<ul class='children'>(.+?)</ul>", re.DOTALL | re.MULTILINE).findall(html)
        #numOfPages = plugin.getSetting('NumOfPages')
        #addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/', 'startPage': '1', 'numOfPages': numOfPages}, {'title':  'Homepage'})
        addon.add_directory({'mode': 'ListSubmenu', 'content': match[0]}, {'title':  'Tamil'})
        addon.add_directory({'mode': 'ListSubmenu', 'content': match[1]}, {'title':  'Hindi'})
        addon.add_directory({'mode': 'ListSubmenu', 'content': match[2]}, {'title':  'Telugu'})
        addon.add_directory({'mode': 'ListSubmenu', 'content': match[3]}, {'title':  "Malayalam"})
        addon.add_directory({'mode': 'ListSubmenu', 'content': match[4]}, {'title':  "Others"})
        addon.add_directory({'mode': 'ListSubmenu', 'content': match[5]}, {'title':  "Genres"})
        addon.add_directory({'mode': 'ListSubmenu', 'content': match[6]}, {'title':  "A-Z"})
        addon.add_directory({'mode': 'ListSubmenu', 'content': match[7]}, {'title':  "Artist"})
        addon.add_directory({'mode': 'GetSearchQuery'},  {'title':  'Search'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def ListSubmenu(content):
        print 'in ListSubmenu'
        numOfPages = plugin.getSetting('NumOfPages')
        match = re.compile('href="(.+?)".*?>(.+?)<', re.DOTALL | re.MULTILINE).findall(content)
        for url, title in match:
                title = HTMLParser.HTMLParser().unescape(title)
                addon.add_directory({'mode': 'GetTitles', 'url': url, 'startPage': '1', 'numOfPages': numOfPages}, {'title':  title})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def BrowseGenre(content):
        numOfPages = plugin.getSetting('NumOfPages')
        match = re.compile('href="(.+?)".*?>(.+?)<', re.DOTALL | re.MULTILINE).findall(content)
        for url, title in match:
                title = HTMLParser.HTMLParser().unescape(title)
                addon.add_directory({'mode': 'GetTitles', 'url': url, 'startPage': '1', 'numOfPages': numOfPages}, {'title':  title})
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
        url = BASE_URL + '/?s='  + unicode_urlencode(query)
        print 'search url is %s ' % url
        GetTitles(url, '1', '1')

def unicode_urlencode(value): 
	if isinstance(value, unicode): 
		return urllib.quote(value.encode("utf-8"))
	else: 
		return urllib.quote(value)


if mode == 'main': 
	MainMenu()
elif mode == 'BrowseGenre':
	BrowseGenre(content)
elif mode == 'GetTitles': 
	GetTitles(url, startPage, numOfPages)
elif mode == 'ListSubmenu': 
	ListSubmenu(content)
elif mode == 'GetLinks':
	GetLinks(url)
elif mode == 'GetSearchQuery':
	GetSearchQuery()
elif mode == 'Search':
	Search(query)
elif mode == 'PlayVideo':
	PlayVideo(url, listitem)

