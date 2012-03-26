import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string, sys, os
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net

BASE_URL = 'http://www.movie2k.to/'
net = Net()
addon = Addon('plugin.video.movie2k', sys.argv)

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)

print 'Mode: ' + str(mode)
print 'URL: ' + str(url)

def GetTitles(url): # Get Movie Titles
        print 'Desirulez get Movie Titles Menu'
        html = net.http_GET(url).content
        match = re.compile('<div style="float:.+?<a href="(.+?)".+?<img src="(.+?)".+?title="(.+?)"').findall(html)
        for url, img, name in match:
                match = re.compile('watch (.+?) online for free').findall(name)
                if len(match) > 0:
                        name = match[0]
                addon.add_directory({'mode': 'GetLinks', 'url': BASE_URL + url}, {'title':  name}, img=img)
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetLinks(url): # Get Movie Links
        print 'In GetLinks'
        html = net.http_GET(url).content
        m = re.search('tablemoviesindex2', html)
        html = html[m.start():]
        m = re.search('tdmoviesheader', html)
        html = html[:m.start()]
        html = re.sub('\\"', '"', html)
        print html
        match = re.compile('href="(.+?)".+?alt="(.+?) .+?alt="Movie quality (.+?)"').findall(html)
        sources = []
        count = 1
        for url, name, quality in match:
                name = str(count) + ": " + name + ' - ' + quality
                url = BASE_URL + url
		url = GetMirror(url)
		hosted_media = urlresolver.HostedMediaFile(url=url, title=name)
		sources.append(hosted_media)
		count = count + 1
	source = urlresolver.choose_source(sources)
	if source: stream_url = source.resolve()
	else: stream_url = ''
	listitem = xbmcgui.ListItem()
	xbmc.Player().play(stream_url, listitem)

def GetMirror(url):
        #print 'in mirror %s' % url
        html = net.http_GET(url).content
        match = re.compile('<a target="_blank" href="(.+?)"').findall(html)
        if len(match) == 0:
                match = re.compile('<iframe src="(.+?)" width=').findall(html)
                if len(match) == 0:
                        match = re.compile('value="config=(.+?)"').findall(html)
                        if len(match) == 0:
                                return url
        #print 'miror is %s ' % match[0]
        if 'sockshare.com/embed' in match[0] or 'putlocker.com/embed' in match[0]:
                match[0] = match[0].replace(
        return match[0]

def MainMenu():  #homescreen
	print 'movie2k home menu'
	#addon.add_directory({'mode': 'LoadCategories', 'url': BollywoodUrl}, {'title':  'Hindi'})
	#addon.add_directory({'mode': 'LoadCategories', 'url': TamilUrl}, {'title':  'Tamil'})
	#addon.add_directory({'mode': 'LoadCategories', 'url': TeluguUrl}, {'title':  'Telugu'})
	#addon.add_directory({'mode': 'LoadCategories', 'url': KannadaUrl}, {'title':  'Kannada'})
	#addon.add_directory({'mode': 'LoadCategories', 'url': DocumentaryUrl}, {'title':  'Documentary'})
	addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL}, {'title':  'Home'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        
def LoadCategories(url): #Categories
        addon.add_directory({'mode': 'GetTitles', 'url': url}, {'title':  'Latest & Exclusive'})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

if mode == 'main': 
	MainMenu()
elif mode == 'LoadCategories': 
	LoadCategories(url)
elif mode == 'GetTitles': 
	GetTitles(url)
elif mode == 'GetLinks':
	GetLinks(url)
elif mode == 'ResolverSettings':
        urlresolver.display_settings()

