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


DB = os.path.join(xbmc.translatePath("special://database"), 'oneddl.db')
BASE_URL = 'http://www.oneddl.eu'
net = Net()
addon = Addon('plugin.video.oneddl', sys.argv)

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
section = addon.queries.get('section', None)
query = addon.queries.get('query', None)
startPage = addon.queries.get('startPage', None)
numOfPages = addon.queries.get('numOfPages', None)
listitem = addon.queries.get('listitem', None)
dialog = xbmcgui.Dialog()


def GetTitles(section, url, startPage= '1', numOfPages= '1'): # Get Movie Titles
        print 'oneddl get Movie Titles Menu %s' % url

        # handle paging
        pageUrl = url
        if int(startPage) > 1:
                pageUrl = url + 'page/' + startPage
        print pageUrl
        html = net.http_GET(pageUrl).content
        start = int(startPage)
        end = start + int(numOfPages)
        last = 2
        match  = re.search("/([\d]+)/' class='last'", html)
        if match:
                last = int(match.group(1))

        print str(start) + ' : ' + str(end) + ' : ' + str(last)
        for page in range( start, min(last, end)):
                if ( page != start):
                        pageUrl = url + 'page/' + str(page)
                        html = net.http_GET(pageUrl).content
                ListTitles(section, html)
       	if end < last:
                addon.add_directory({'mode': 'GetTitles', 'section': section, 'url': url, 'startPage': str(end), 'numOfPages': numOfPages}, {'title':  'Next..'})
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def ListTitles(section, html):
        print ' in ListTitles'
        #match = re.compile('entry clearfix.+?href="(.+?)">(.+?)<.+?href="(.+?)"(.+?)<div.+?<p.*?>(.+?)<.+?/title/(.+?)/.+?Download.+?</div>(.+?)</div>', re.DOTALL).findall(html)
        #for url, title, img, info, plot, imdbid, content in match:

        if 'movies' in section:
                match = re.compile('entry-title"><a href="(.+?)".+?center"><img src="(.+?)" title="(.+?)".+?href="(.+?)"', re.DOTALL).findall(html)
                for url, img, title, imdbUrl in match:
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': url}, {'title':  title.decode('utf-8')}, img= img)
        else:
                match = re.compile('entry-title"><a href="(.+?)".+?>(.+?)<.+?<p align="center"><img src="(.+?)"', re.DOTALL).findall(html)
                for url, title, img in match:
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': url}, {'title':  title.decode('utf-8')}, img= img)


def GetLinks(section, url): # Get TV Links
        
        print 'In GetLinks %s' % url
        html = net.http_GET(url).content

        r = re.search('oneclickimg', html)
        content = html[r.end():]
        if not r:
                dialog.ok(' OneDDL ', ' No Streaming links found. ', '', '')
        if 'movies' in section:
                r = re.search('downloadimg', content)
        else:
                r = re.search('id="download-links"', content)
        if not r:
                dialog.ok(' OneDDL ', ' No Streaming links found. ', '', '')
        content = content[:r.start()]
        
        match = re.compile('<strong>(.+?)</strong>.+?href="(.+?)"', re.DOTALL).findall(content)
        listitem = GetMediaInfo(html)
        for host, url in match:
                #if urlresolver.HostedMediaFile(host=host.lower(), media_id='xxx'):
                addon.add_directory({'mode': 'PlayVideo', 'url': url, 'listitem': listitem}, {'title':  host })
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def PlayVideo(url, listitem):
        print 'in PlayVideo %s' % url
        url = net.http_GET(url).get_url()
        if urlresolver.HostedMediaFile(url= url):
                stream_url = urlresolver.HostedMediaFile(url).resolve()
                xbmc.Player().play(stream_url, listitem)
        else:
                dialog.ok(' OneDDL ', ' Could not find video. ', '', '')

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
        CAT_BASE_URL = BASE_URL + '/category/' + section + '/'
        addon.add_directory({'mode': 'GetTitles', 'section': section, 'url': BASE_URL + '/category/' + section + '/',
                             'startPage': '1', 'numOfPages': '2'}, {'title':  'All'})
        match = re.compile(CAT_BASE_URL + '(.+?)/">(.+?)<').findall(html)
        for cat, title in match:
                url = CAT_BASE_URL + cat + '/'
                if 'Complete BluRay' in title:
                        continue
                addon.add_directory({'mode': 'GetTitles', 'section': section, 'url': url,
                                     'startPage': '1', 'numOfPages': '2'}, {'title':  title})
        
        addon.add_directory({'mode': 'GetSearchQuery', 'section': section},  {'title':  'Search'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MainMenu():    #homescreen
        addon.add_directory({'mode': 'Categories', 'section': 'movies'},  {'title':  'Movies'})
        addon.add_directory({'mode': 'Categories', 'section': 'tv-shows'},  {'title':  'TV Shows'})
        addon.add_directory({'mode': 'GetTitles', 'section': 'ALL', 'url': BASE_URL + '/category/staff-picks/', 'startPage': '1', 'numOfPages': '2'}, {'title':  'Staff Picks'})
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
	GetLinks(section, url)
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
