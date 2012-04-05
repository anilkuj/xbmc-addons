import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string, sys, os
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
from metahandler import metahandlers


try:
	from sqlite3 import dbapi2 as sqlite
	print "Loading sqlite3 as DB engine"
except:
	from pysqlite2 import dbapi2 as sqlite
	print "Loading pysqlite2 as DB engine"


prepare_zip = False
metaget=metahandlers.MetaData(preparezip=prepare_zip)

addon_id = 'plugin.video.oneclickmoviez'
plugin = xbmcaddon.Addon(id=addon_id)

DB = os.path.join(xbmc.translatePath("special://database"), 'oneclickmoviez.db')
BASE_URL = 'http://oneclickmoviez.com/'
net = Net()
addon = Addon('plugin.video.oneclickmoviez', sys.argv)

hideAdult = True
autoPlay = True
enableMeta = True

if plugin.getSetting('hideAdult') == 'false':
        hideAdult = False

if plugin.getSetting('autoPlay') == 'false':
        autoPlay = False

if plugin.getSetting('enableMeta') == 'false':
        enableMeta = False

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
title = addon.queries.get('title', None)
year = addon.queries.get('year', None)



def GetTitles(section, url, startPage= '1', numOfPages= '1'): # Get Movie Titles
        print 'oneclickmoviez get Movie Titles Menu %s' % section

        # handle paging
        pageUrl = url
        if int(startPage)> 1:
                pageUrl = url + 'page/' + startPage + '/'
        html = net.http_GET(pageUrl).content

        start = int(startPage)
        end = start + int(numOfPages)
        print str(start) + ' : ' + str(end)
        for page in range( start, end):
                print 'in for loop'
                if ( page != start):
                        pageUrl = url + 'page/' + str(page) + '/'
                        html = net.http_GET(pageUrl).content
                match = re.compile('<h2><a href=(.+?)</a></p>', re.DOTALL).findall(html)
                for content in match:
                        if section == 'tvshow':
                                ListTVTitle(section, content)
                        else:
                                ListMovieTitle(section, content)

                if 'Previous Entries' not in html:
                        break
        # keep iterating until the laast page is reached
        if 'Previous Entries' in html:
                addon.add_directory({'mode': 'GetTitles', 'section': section, 'url': url, 'startPage': str(end), 'numOfPages': numOfPages}, {'title': 'Next...'})
        
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def ListTVTitle(section, content):
        print 'in ListTVTitle'
        match = re.compile('"(.+?)".+?>(.+?)<.+?src="(.+?)"', re.DOTALL).findall(content)
        for url, name, img in match:
                meta = {}
                r = re.search( '^(.+?) S\d\d', name.strip())
                title = name
                if r:
                        title = r.group(1)
                if enableMeta:
                        try:
                                meta = metaget.get_meta(section, title)
                        except Exception, e:
                                print '************* Error querying metadata: %s' % e
                                meta['title'] = name
                                meta['backdrop_url'] = ''
                                meta['cover_url'] = img

                        #if meta['cover_url'] in ('/images/noposter.jpg',''):
                        meta['cover_url'] = img
                                
                        if meta['title']:
                                name = meta['title']
                else:
                        meta['title'] = name
                        meta['backdrop_url'] = ''
                        meta['cover_url'] = img
                        
                addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': url, 'title': name, 'year': year}, meta,
                                            img= meta['cover_url'], fanart= meta['backdrop_url'])

def  ListMovieTitle(section, content):
        print 'in ListMovieTitle'
        match = re.compile('"(.+?)".+?>(.+?)<.+?src="(.+?)".+?\.com/([\w\./:]+)" target="_blank">IMDB', re.DOTALL).findall(content)
        for url, name, img, imdbUrl in match:
                meta = {}
                r = re.search('^(.+?) [\[]*([\d][\d][\d][\d])[\]]*', name.strip())
                year = ''
                title = name
                if r:
                        title, year = r.groups()
                imdbId = GetImdbId(imdbUrl)
                cm = []
                if enableMeta:
                        try:
                                #print imdbId + ' : ' + title + ' : ' + year
                                if imdbId:
                                        meta = metaget.get_meta(section, title, year= year, imdb_id= imdbId )
                                else:
                                        meta = metaget.get_meta(section, title, year= year)
                        except Exception, e:
                                print '************* Error querying metadata: %s' % e
                                meta['title'] = name
                                meta['backdrop_url'] = ''
                                meta['cover_url'] = img

                        if meta['cover_url'] in ('/images/noposter.jpg',''):
                                print 'in if'
                                meta['cover_url'] = img

                        print 'imdb title is %s' % meta['title']
                        if meta['title']:
                                name = meta['title']

                        if 'trailer_url' in meta and meta['trailer_url']:
                                trurl = meta['trailer_url']
                                trurl = re.sub('&feature=related','',trurl)
                                trurl = trurl.encode('base-64').strip()
                                #runstring = 'XBMC.Container.Update(%s?mode=PlayTrailer&url=%s)' %(sys.argv[0], trurl)
                                runstring = 'XBMC.RunPlugin(%s?mode=PlayTrailer&url=%s)' %(sys.argv[0], trurl)
                                cm.append(('Watch Trailer', runstring))
                        cm.append(('Show Information', 'XBMC.Action(Info)'))
                else:
                        meta['title'] = name
                        meta['backdrop_url'] = ''
                        meta['cover_url'] = img
                
                try:        
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': url, 'title': name, 'year': year}, meta,
                                            img= meta['cover_url'], fanart= meta['backdrop_url'], contextmenu_items= cm, context_replace=True)
                except UnicodeEncodeError, err:
                        meta['title'] = meta['title'].encode('utf-8')
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': url, 'title': title, 'year': year}, meta,
                                            img= meta['cover_url'], fanart= meta['backdrop_url'], contextmenu_items= cm, context_replace=True)
                except UnicodeDecodeError, err:
                        meta['title'] = meta['title'].decode('utf-8')
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': url, 'title': title, 'year': year}, meta,
                                            img= meta['cover_url'], fanart= meta['backdrop_url'], contextmenu_items= cm, context_replace=True)
                

def PlayTrailer(url):
	url = url.decode('base-64')
	print 'Attempting to resolve and play trailer at %s' % url
	sources = []
	hosted_media = urlresolver.HostedMediaFile(url=url)
	sources.append(hosted_media)
	source = urlresolver.choose_source(sources)
	if source: stream_url = source.resolve()
	else: stream_url = ''
	xbmc.Player().play(stream_url)

def GetImdbId(imdbUrl):
        print 'imdbUrl is %s' % imdbUrl
        imdbId = None
        match = re.search('/title/(.+?)/', imdbUrl)
        if match:
                imdbId = match.group(1)
                return imdbId
        url = net.http_GET(BASE_URL + imdbUrl).get_url()
        match = re.search('/title/(.+?)/', url)
        if match:
                imdbId = match.group(1)
        return imdbId        

        
def GetLinks(url, title='', year='0'): # Get Links
        print 'In GetLinks %s' % url
        html = net.http_GET(url).content
        listitem = GetMediaInfo(title, year)

        content = html
        r = re.search('</strong></span>', html)
        if r:
                content = html[r.end():]

        r = re.search('<div class="tags"> </div>', content)
        if r:
                content = content[:r.start()]
                
        match = re.compile('href="(.+?)"').findall(content)
        autoUrl = None
        for url in match:
                try:
                        host = GetDomain(url)
                        
                        if 'Unknown' in host:
                                continue

                        if 'oneclick' in host:
                                url = net.http_GET(url).get_url()
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
                                        
                                title = url.rpartition('/')
                                title = title[2].replace('.html', '')
                                title = title.replace('.htm', '')
                                addon.add_directory({'mode': 'PlayVideo', 'url': url, 'listitem': listitem}, {'title':  host + ' : ' + title})
                except:
                        continue

        find = re.search('<table border="0" width="90%"', html)
        if find:
                html = html[find.end():]
                match = re.compile('<a href="(.+?)" rel="nofollow"', re.DOTALL).findall(html)
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


def GetMediaInfo(title, year):
        print 'In GetMediaInfo'
        print title
        print year
        if not year:
                year = '0'
        listitem = xbmcgui.ListItem()
        try:
                listitem.setInfo('video', {'Title': title, 'Year': int(year) } )
        except:
                listitem.setInfo('video', {'Title': title, 'Year': 0 } )
        return listitem

def Categories():  #categories

        html = net.http_GET(BASE_URL).content
        match = re.compile('<li class="cat-item.+?href="(.+?)".+?>(.+?)<').findall(html)
        for url, title in match:
                if 'Adult' in title and hideAdult:
                        continue

                if 'tv-packs' in url or 'Adult' in title:
                        addon.add_directory({'mode': 'GetTitles', 'section': 'tvshow', 'url': url, 'startPage': '1', 'numOfPages': '1'}, {'title':  title})
                else:
                        addon.add_directory({'mode': 'GetTitles', 'section': 'movie', 'url': url, 'startPage': '1', 'numOfPages': '1'}, {'title':  title})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def MainMenu():    #homescreen
        addon.add_directory({'mode': 'GetTitles', 'section': 'movie', 'url': BASE_URL, 'startPage': '1', 'numOfPages': '1'}, {'title':  'Homepage'})
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
        url = BASE_URL + '?s='  + query
        GetTitles('movie', url, startPage= '1', numOfPages= '1')


if mode == 'main': 
	MainMenu()
elif mode == 'GetTitles': 
	GetTitles(section, url, startPage, numOfPages)
elif mode == 'GetLinks':
	GetLinks(url, title, year)
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
elif mode == 'PlayTrailer':
        PlayTrailer(url)
