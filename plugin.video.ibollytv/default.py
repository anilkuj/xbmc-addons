import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string, sys, os
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net

BollywoodUrl = 'http://www.ibollytv.com/ihindi.php'
TamilUrl = 'http://www.ibollytv.com/itamil.php'
TeluguUrl = 'http://www.ibollytv.com/itelugu.php'
KannadaUrl = 'http://www.ibollytv.com/ikannada.php'
DocumentaryUrl = 'http://www.ibollytv.com/idocumentary.php'

BASE_URL = 'http://www.ibollytv.com'
net = Net()
addon = Addon('plugin.video.ibollytv', sys.argv)

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)

print 'Mode: ' + str(mode)
print 'URL: ' + str(url)

def GetTitles(url): # Get Movie Titles
        print 'Desirulez get Movie Titles Menu'
        html = net.http_GET(url).content
        match = re.compile('src="(.+?).+?href="(.+?)">(.+?)<').findall(html)
        for img, url, name in match:
                addon.add_directory({'mode': 'GetLinks', 'url': BASE_URL + url}, {'title':  name}, img=img)
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetLinks(url): # Get Movie Links
        print 'In GetLinks'
        html = net.http_GET(url).content
        match = re.compile('href="(.+?)".+?>>>.+?(.+?) Parts').findall(html)
        sources = []
        for url, parts in match:
                parts = parts[-1:]
                print 'Source found:\n url %s\n part %s\n' % (url, parts)
		
                for n in range(0, int(parts)):
                        page = str(n + 1)
                        print 'in for loop '+ page
                        link, title = GetVideoLink(url, page, int(parts))
                        print 'link is %s title is %s' %(link, title)
                        hosted_media = urlresolver.HostedMediaFile(url=link, title=title)
                        sources.append(hosted_media)
		
	source = urlresolver.choose_source(sources)
	if source: stream_url = source.resolve()
	else: stream_url = ''
	listitem = xbmcgui.ListItem()
	xbmc.Player().play(stream_url, listitem)

def GetVideoLink( url, part, totalParts):
        print 'in GetVideoLink'
        pageURL = url + '&page=' + part
        html = net.http_GET(pageURL).content
        match = re.compile("class='brokenaclass' href='(.+?)'").findall(html)
        print ' match is %s ' % match[0]
        return match[0], GetVideoTitle(match[0], part, totalParts)

def GetVideoTitle( url, part, totalParts):
        print 'in GetVideoTitle'
        tmp = re.compile('//(.+?)/').findall(url)
        if len(tmp) == 0:
            return "Part "+part
        print 'r is %s ' % tmp[0]
        domain = tmp[0].replace('www.', '')
        domain = domain.replace('embed.', '')
        print 'domain is %s ' % domain
        if totalParts == 1:
                return domain
        else:
                return domain + " Part "+ part

def MainMenu():  #homescreen
	print 'ibollytv home menu'
	addon.add_directory({'mode': 'LoadCategories', 'url': BollywoodUrl}, {'title':  'Hindi'})
	addon.add_directory({'mode': 'LoadCategories', 'url': TamilUrl}, {'title':  'Tamil'})
	addon.add_directory({'mode': 'LoadCategories', 'url': TeluguUrl}, {'title':  'Telugu'})
	addon.add_directory({'mode': 'LoadCategories', 'url': KannadaUrl}, {'title':  'Kannada'})
	addon.add_directory({'mode': 'LoadCategories', 'url': DocumentaryUrl}, {'title':  'Documentary'})
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

