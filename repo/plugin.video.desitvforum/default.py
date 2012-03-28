import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
import unicodedata


BollywoodLatestUrl = 'http://tv.desitvforum.net/index.php?option=com_content&task=category&sectionid=61&id=892&Itemid=86&filter=watch+online&limit=100'
BASE_URL = 'http://tv.desitvforum.net/'
net = Net()
addon = Addon('plugin.video.desitvforum', sys.argv)
scrape_regex_1 = 'href="(.+?)" target="_blank">(.+?)<'

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
regex = addon.queries.get('regex', None)

print 'Mode: ' + str(mode)
print 'URL: ' + str(url)

def GetTitles(url): # Get Movie Titles
        print 'desitvforum get Movie Titles Menu'
        html = net.http_GET(url).content
        html = html[re.search('sectiontableheader', html).end():]
        match = re.compile('<a href="(.+?)">.+?([\w][\w\s\(\)\]\[-]+) Watch', re.MULTILINE | re.DOTALL).findall(html)
        for link, name in match:
                link = unicode_urlencode(BASE_URL +link)
                liurl = sys.argv[0] + '?mode=GetLinks&url=' + link
                li = xbmcgui.ListItem(name)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=liurl, listitem=li, isFolder=True )
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def unicode_urlencode(value): 
	if isinstance(value, unicode): 
		return urllib.quote(value.encode("utf-8"))
	else: 
		return urllib.quote(value)

def GetLinks(url): # Get Movie Links
        url = url.replace('amp;', '')
        print 'In GetLinks %s' % url
        html = net.http_GET(url).content
        match = re.search( 'contentpaneopen', html )
        html = html[match.end():]
        match = re.search( 'contentpaneopen', html )
        html = html[match.end():]
        match = re.compile(scrape_regex_1, re.MULTILINE | re.DOTALL).findall(html)
        sources = []
        for url, name in match:
                if '-' in name:
                        match = re.search( '-', name)
                        name = GetDomain(url) + ' - ' + name[match.end():]
                else:
                        name = GetDomain(url)
		hosted_media = urlresolver.HostedMediaFile(url=url, title=name)
		sources.append(hosted_media)
	source = urlresolver.choose_source(sources)
	if source: stream_url = source.resolve()
	else: stream_url = ''
	listitem = xbmcgui.ListItem("")
	xbmc.Player().play(stream_url, listitem)

def GetDomain(url):
        tmp = re.compile('//(.+?)/').findall(url)
        domain = 'Unknown'
        if len(tmp) > 0 :
            domain = tmp[0].replace('www.', '')
        return domain

def MainMenu():  #homescreen
	print 'desitvforum home menu'
        addon.add_directory({'mode': 'GetTitles', 'url': BollywoodLatestUrl}, {'title':  'Latest & Exclusive'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode == 'main': 
	MainMenu()
elif mode == 'GetTitles': 
	GetTitles(url)
elif mode == 'GetLinks':
	GetLinks(url)
elif mode == 'ResolverSettings':
        urlresolver.display_settings()

