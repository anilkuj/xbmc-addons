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


DB = os.path.join(xbmc.translatePath("special://database"), 'tamilmusix.db')
BASE_URL = 'http://www.tamilmusix.com'
net = Net()
addon = Addon('plugin.video.tamilmusix', sys.argv)

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
section = addon.queries.get('section', None)
query = addon.queries.get('query', None)
startPage = addon.queries.get('startPage', None)
numOfPages = addon.queries.get('numOfPages', None)
content = addon.queries.get('content', None)
listitem = addon.queries.get('listitem', None)


def GetTitles(section, url, startPage= '1', numOfPages= '1'): # Get Movie Titles
        print 'tamilmusix get Movie Titles Menu %s' % url

        # handle paging
        pageUrl = url
        if int(startPage) > 1:
                pageUrl = url + '/page/' + startPage
        print pageUrl
        html = net.http_GET(pageUrl).content
        start = int(startPage)
        end = start + int(numOfPages)
        last = 2
        match  = re.compile("/page/.+?>(.+?)<").findall(html)
        if len(match) > 0:
                last = int(match[len(match) - 2]) + 1

        print str(start) + ' : ' + str(end) + ' : ' + str(last)
        for page in range( start, min(last, end)):
                if ( page != start):
                        pageUrl = url + '/page/' + str(page)
                        html = net.http_GET(pageUrl).content
                ListTitles(section, html)
       	if end < last:
                addon.add_directory({'mode': 'GetTitles', 'section': section, 'url': url, 'startPage': str(end), 'numOfPages': numOfPages}, {'title':  'Next..'})
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def ListTitles(section, html):
        print ' in ListTitles'
        match = re.compile('postcontent">.+?href="(.+?)".+?src="(.+?)".+?alt=\'(.+?)\'', re.DOTALL).findall(html)
        for url, img, title in match:
                addon.add_directory({'mode': 'GetLinks', 'url': url}, {'title':  title}, img= img)


def GetLinks(url): # Get TV Links
        print 'In GetLinks %s' % url
        html = net.http_GET(url).content
        match = re.compile('et-box-content(.+?)</div>', re.DOTALL).findall(html)
        listitem = GetMediaInfo(html)
        for content in match:
                print 'in first loop'
                links = re.compile('href="(.+?)".+?>(.+?)<', re.DOTALL).findall(content)
                for url, name in links:
                        print 'in second loop'
                        if 'adf.ly' in url:
                                url = GetAdflyUrl(url)
                        if not url:
                                print 'could not resolve ad.fly url'
                                continue
                        print url

                        # ignore .rar files
                        r = re.search('\.rar[(?:\.html|\.htm)]*', url, re.IGNORECASE)
                        if r:
                                print 'ignored desirulez url %s' % url
                                continue

                        # ignore .rar files
                        r = re.search('\.rar[(?:\.html|\.htm)]*', name, re.IGNORECASE)
                        if r:
                                print 'ignored desirulez url %s' % name
                                continue
                        

                        
                        host = GetDomain(url)
                        #print '*****************************' + host +  ':' + name + ' : ' + url
                        if urlresolver.HostedMediaFile(url= url):
                                addon.add_directory({'mode': 'PlayVideo', 'url': url, 'listitem': listitem}, {'title':  host + ' : ' + name})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetAdflyUrl(url):
        print 'in GetAdflyUrl %s' % url
        html = net.http_GET(url).content
        match = re.search("var url = '(.+?)';", html)
        if match:
                url =  match.group(1)
                return net.http_GET(url).get_url()
        else:
                return None

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
        BASE_CAT_URL = BASE_URL + '/category/' + section 
        match = re.compile('<li id=.+?href="' + BASE_CAT_URL + '(.+?)">(.+?)<').findall(html)
        for cat, title in match:
                url = BASE_CAT_URL + cat
                if 'Movie' in title:
                        addon.add_directory({'mode': 'GetTitles', 'section': section, 'url': url, 'startPage': '1', 'numOfPages': '2'}, {'title':  title})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MainMenu():    #homescreen
        addon.add_directory({'mode': 'Categories', 'section': 'tamil'},  {'title':  'Tamil'})
        addon.add_directory({'mode': 'Categories', 'section': 'hindi'},  {'title':  'Hindi'})
        addon.add_directory({'mode': 'Categories', 'section': 'telugu'},  {'title':  'Telugu'})
        addon.add_directory({'mode': 'Categories', 'section': 'malayalam'},  {'title':  'Malayalam'})
        addon.add_directory({'mode': 'Categories', 'section': 'english'},  {'title':  'English'})
        addon.add_directory({'mode': 'GetSearchQuery', 'section': section},  {'title':  'Search'})        
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def ListMovies(section, url):
        match = re.compile('href="(.+?)">(.+?)<').findall(content)
        for url, title in match:
                addon.add_directory({'mode': 'GetTitles', 'section': section, 'url': url, 'startPage': '1', 'numOfPages': '2'}, {'title':  title.encode('utf-8')})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def BrowseGenre(content):
        match = re.compile('href="(.+?)">(.+?)<').findall(content)
        for url, title in match:
                addon.add_directory({'mode': 'GetLinks', 'url': url, 'startPage': '1', 'numOfPages': '3'}, {'title':  title.encode('utf-8')})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetSearchQuery(section):
	last_search = addon.load_data('search')
	if not last_search: last_search = ''
	keyboard = xbmc.Keyboard()
        keyboard.setHeading('Search TV Shows')
	keyboard.setDefault(last_search)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
                query = keyboard.getText()
                addon.save_data('search',query)
                Search(section, query)
	else:
                return

def Search(section, query):
        url = BASE_URL + '/?s='  + query
        print url
        GetTitles(section, url, startPage= '1', numOfPages= '1')

if mode == 'main': 
	MainMenu()
elif mode == 'BrowseGenre':
	BrowseGenre(content)
elif mode == 'GetTitles': 
	GetTitles(section, url, startPage, numOfPages)
elif mode == 'ListMovies': 
	ListMovies(section, url)
elif mode == 'GetLinks':
	GetLinks(url)
elif mode == 'GetSearchQuery':
	GetSearchQuery(section)
elif mode == 'Search':
	Search(query)
elif mode == 'Categories':
	Categories(section)
elif mode == 'ResolverSettings':
        urlresolver.display_settings()
elif mode == 'PlayVideo':
	PlayVideo(url, listitem)
