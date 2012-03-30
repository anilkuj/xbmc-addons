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

addon_id = 'plugin.video.oneclickmoviez'
plugin = xbmcaddon.Addon(id=addon_id)

DB = os.path.join(xbmc.translatePath("special://database"), 'oneclickmoviez.db')
BASE_URL = 'http://oneclickmoviez.com/'
net = Net()
addon = Addon('plugin.video.oneclickmoviez', sys.argv)

hideAdult = True
autoPlay = True

if plugin.getSetting('hideAdult') == 'false':
        hideAdult = False

if plugin.getSetting('autoPlay') == 'false':
        autoPlay = False

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
content = addon.queries.get('content', None)
query = addon.queries.get('query', None)
startPage = addon.queries.get('startPage', None)
numOfPages = addon.queries.get('numOfPages', None)
listitem = addon.queries.get('listitem', None)
urlList = addon.queries.get('urlList', None)
section = addon.queries.get('section', None)



def GetTitles(url, startPage= '1', numOfPages= '1'): # Get Movie Titles
        print 'oneclickmoviez get Movie Titles Menu %s' % url

        # handle paging
        pageUrl = url
        if int(startPage)> 1:
                pageUrl = url + 'page/' + startPage + '/'
        print pageUrl
        html = net.http_GET(pageUrl).content

        start = int(startPage)
        end = start + int(numOfPages)

        for page in range( start, end):
                if ( page != start):
                        pageUrl = url + 'page/' + str(page) + '/'
                        html = net.http_GET(pageUrl).content
                        
                match = re.compile('#content.+?href="(.+?)".+?>(.+?)<.+?src="(.+?)"', re.DOTALL).findall(html)
                for movieUrl, name, img in match:
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': movieUrl}, {'title':  name.strip()}, img= img)
                if 'Previous Entries' not in html:
                        break

        # keep iterating until the laast page is reached
        if 'Previous Entries' in html:
                addon.add_directory({'mode': 'GetTitles', 'url': url, 'startPage': str(end), 'numOfPages': numOfPages}, {'title': 'Next...'})
        
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetLinks(url): # Get Links
        print '***************************************************** In GetLinks %s' % url
        html = net.http_GET(url).content
        listitem = GetMediaInfo(html)
        content = html
        r = re.search('</strong></span>', html)
        if r:
                content = html[r.end():]

        r = re.search('<div class="tags"> </div>', content)
        if r:
                content = content[:r.start()]
                
        match = re.compile('href="(.+?)"').findall(content)
        listitem = GetMediaInfo(content)
        autoUrl = None
        for url in match:
                try:
                        host = GetDomain(url)
                        
                        if 'Unknown' in host:
                                continue

                        if 'oneclick' in host:
                                url = net.http_GET(url).get_url()
                                print 'redirect url is %s' % url
                                if '?' in url:
                                        link = url.partition('?')
                                        url = link[2]
                                        if 'pastebin.com' in url:
                                                html = net.http_GET(url).content
                                                links = re.findall('><div class=.+?>(.+?)<', html)
                                                match.extend(links)
                                                continue
                                        host = GetDomain(url)
                                else:
                                        continue
                                
                        # ignore .rar files
                        r = re.search('\.rar[(?:\.html|\.htm)]*', url, re.IGNORECASE)
                        if r:
                                continue
                        print '*****************************' + host + ' : ' + url
                        if urlresolver.HostedMediaFile(url= url):

                                if not autoUrl and 'megashare' in url:
                                        autoUrl = url
                                        
                                print 'in GetLinks if loop'
                                title = url.rpartition('/')
                                title = title[2].replace('.html', '')
                                title = title.replace('.htm', '')
                                addon.add_directory({'mode': 'PlayVideo', 'url': url, 'listitem': listitem}, {'title':  host + ' : ' + title})
                except:
                        continue

        find = re.search('<table border="0" width="90%"', html)
        if find:
                print 'in comments if'
                html = html[find.end():]
                match = re.compile('<a href="(.+?)" rel="nofollow"', re.DOTALL).findall(html)
                print len(match)
                for url in match:
                        host = GetDomain(url)
                        if 'Unknown' in host:
                                continue
                        
                        # ignore .rar files
                        r = re.search('\.rar[(?:\.html|\.htm)]*', url, re.IGNORECASE)
                        if r:
                                continue
                        try:
                                if urlresolver.HostedMediaFile(url= url):
                                        print 'in GetLinks if loop'
                                        title = url.rpartition('/')
                                        title = title[2].replace('.html', '')
                                        title = title.replace('.htm', '')
                                        addon.add_directory({'mode': 'PlayVideo', 'url': url, 'listitem': listitem}, {'title':  host + ' : ' + title})
                        except:
                                continue
        if autoPlay and autoUrl:
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
                print match.group(1) + ' : '  + match.group(2)
                listitem.setInfo('video', {'Title': match.group(1), 'Year': int(match.group(2)) } )
        return listitem

def Categories():  #categories

        html = net.http_GET(BASE_URL).content
        match = re.compile('<li class="cat-item.+?href="(.+?)".+?>(.+?)<').findall(html)
        for url, title in match:
                if 'Adult' in title and hideAdult:
                        continue
                addon.add_directory({'mode': 'GetTitles', 'url': url, 'startPage': '1', 'numOfPages': '2'}, {'title':  title})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MainMenu():    #homescreen
        addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL, 'startPage': '1', 'numOfPages': '2'}, {'title':  'Homepage'})
        addon.add_directory({'mode': 'Categories'},  {'title':  'Categories'})
        addon.add_directory({'mode': 'GetSearchQuery'},  {'title':  'Search'})
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
        url = 'http://www.google.com/search?q=site:oneclickmoviez.com ' + query
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
elif mode == 'GetTitles': 
	GetTitles(url, startPage, numOfPages)
elif mode == 'GetLinks':
	GetLinks(url)
elif mode == 'GetSearchQuery':
	GetSearchQuery()
elif mode == 'Search':
	Search(query)
elif mode == 'PlayVideo':
	PlayVideo(url, listitem)	
elif mode == 'ResolverSettings':
        urlresolver.display_settings()
elif mode == 'Categories':
        Categories()
