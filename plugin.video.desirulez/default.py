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

addon_id = 'plugin.video.desirulez'
plugin = xbmcaddon.Addon(id=addon_id)

DB = os.path.join(xbmc.translatePath("special://database"), 'desirulez.db')
BASE_URL = 'http://www.desirulez.net'
net = Net()
addon = Addon('plugin.video.desirulez', sys.argv)
showAllParts = True
showPlayAll = True

if plugin.getSetting('showAllParts') == 'false':
        showAllParts = False

if plugin.getSetting('showPlayAll') == 'false':
        showPlayAll = False

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
content = addon.queries.get('content', None)
query = addon.queries.get('query', None)
startPage = addon.queries.get('startPage', None)
numOfPages = addon.queries.get('numOfPages', None)
listitem = addon.queries.get('listitem', None)
urlList = addon.queries.get('urlList', None)


SITES_1 =  ['orphaninneeds.com', 'worldsecurityco.com', 'allvideotv.info', 'estates4u.co', 'priyankhd.in']
SITES_2 =  ['bollymoviz.com', 'videos.desihome.info', 'hd-share.info', 'movierulez.in', 'dohori-sanjh.com']



def GetTitles(url, startPage= '1', numOfPages= '1'): # Get Movie Titles
        print 'desirulez get Movie Titles Menu %s' % url

        # handle paging
        pageUrl = url
        if int(startPage)> 1:
                pageUrl = url + '-' + startPage + '.html'
        print pageUrl
        html = net.http_GET(pageUrl).content

        start = int(startPage)
        end = start + int(numOfPages)
        
        last = 2
        match  = re.search('class="first_last".+?-([\d]+).html', html)
        if match:
                last = int(match.group(1))

        # Get the sticky section only once
        if start == 1:
                match = re.compile('Sticky:.+?href="(.+?)".+?>(.+?)<', re.DOTALL).findall(html)
                for movieUrl, name in match:
                        cm  = []
                        title = name.partition(' ')
                        runstring = 'XBMC.Container.Update(plugin://plugin.video.desirulez/?mode=Search&query=%s)' %(title[0])
        		cm.append(('Search on Desirulez', runstring))
                        addon.add_directory({'mode': 'GetLinks', 'url': movieUrl}, {'title':  name}, contextmenu_items= cm)   

        print str(start) + ' : ' + str(end) + ' : ' + str(last)
        for page in range( start, min(last, end)):
                if ( page != start):
                        pageUrl = url + '-' + str(page) + '.html'
                        html = net.http_GET(pageUrl).content
                        
                match = re.compile('nonsticky.+?<a class=".+?" href="(.+?)".+?>(.+?)<', re.DOTALL).findall(html)
                for movieUrl, name in match:
                        cm  = []
                        title = name.partition(' ')
                        runstring = 'XBMC.Container.Update(plugin://plugin.video.desirulez/?mode=Search&query=%s)' %(title[0])
        		cm.append(('Search on Desirulez', runstring))
                        addon.add_directory({'mode': 'GetLinks', 'url': movieUrl}, {'title':  name}, contextmenu_items= cm) 

        # keep iterating until the laast page is reached
        if end < last:
                addon.add_directory({'mode': 'GetTitles', 'url': url, 'startPage': str(end), 'numOfPages': numOfPages}, {'title': 'Next...'})

       	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetLinks(url): # Get Links
        print '***************************************************** In GetLinks %s' % url
        html = net.http_GET(url).content
        listitem = GetMediaInfo(html)
        
        match = re.compile('<pre class="bbcode_code"style="height:(.+?)</div>', re.DOTALL).findall(html)
        for data in match:
                urlList = []             
                links = re.compile('http(.+?)(?:\n|<|")').findall(data)
                firstPart = True
                print '******************************************************'
                for url in links:

                        if 'http' not in url:
                                url = 'http' + url
                        print url
                        url = url.replace(' ', '')
                        host = GetDomain(url)

                        # Get all mirrors for mirorii.com and it it to links
                        if 'mirorii.com' in url:
                                links.extend(GetMirroriLinks(url))
                                continue
                        if 'multiup.org' in url:
                                links.extend(GetMultiup(url))
                                continue
                        
                        # ignore .rar files
                        r = re.search('\.rar[(?:\.html|\.htm)]*', url, re.IGNORECASE)
                        if r:
                                print 'ignored desirulez url %s' % url
                                continue

                        # ignore .srt files
                        r = re.search('\.srt[(?:\.html|\.htm)]*$', url, re.IGNORECASE)
                        if r:
                                print 'ignored desirulez url %s' % url
                                continue
                        
                        # find parts and build array for plalist
                        r = re.search('\.[0]+([\d]+)[\.]*[(?:html|htm)]*', url, re.IGNORECASE)
                        if r:
                                print 'its a part file'
                                partNum = r.group(1)
                                if firstPart:
                                        print 'in First part'
                                        if len(urlList) > 0:
                                                if showPlayAll and urlresolver.HostedMediaFile(url= urlList[0]):
                                                        print 'adding previous parts'
                                                        title =  GetDomain(urlList[0]) + ' : Play All ' + str(len(urlList)) + ' Parts'
                                                        addon.add_directory({'mode': 'PlayVideo', 'urlList': SortUrlList(urlList), 'listitem': listitem}, {'title': title })
                                                        
                                        urlList = []
                                        firstPart = False
                                urlList.append(url)
                                if showAllParts and urlresolver.HostedMediaFile(url= url):
                                        title = url.rpartition('/')
                                        title = title[2].replace('.html', '')
                                        title = title.replace('.htm', '')
                                        title = GetDomain(url) + ' : ' + title
                                        addon.add_directory({'mode': 'PlayVideo', 'urlList': [url], 'listitem': listitem}, {'title': title })
                                continue
                        else:
                                print 'its a single file'
                                if len(urlList) > 0:
                                        print 'adding previous parts'
                                        if showPlayAll and urlresolver.HostedMediaFile(url= urlList[0]):
                                                print 'adding previous parts'
                                                title =  GetDomain(urlList[0]) + ' : Play All ' + str(len(urlList)) + ' Parts'
                                                addon.add_directory({'mode': 'PlayVideo', 'urlList': urlList, 'listitem': listitem}, {'title': title })
                                print 'single file link'
                                # if its a single link just build array of just that link
                                urlList = []
                                urlList.append(url)
                        
                                if urlresolver.HostedMediaFile(url= urlList[0]):
                                        host = host + ' : Single link'
                                        addon.add_directory({'mode': 'PlayVideo', 'urlList': urlList, 'listitem': listitem}, {'title':  host})
                                        urlList = []
                if len(urlList) > 0:
                        if showPlayAll and urlresolver.HostedMediaFile(url= urlList[0]):
                                title =  GetDomain(urlList[0]) + ' : Play All ' + str(len(urlList)) + ' Parts'
                                addon.add_directory({'mode': 'PlayVideo', 'urlList': SortUrlList(urlList), 'listitem': listitem}, {'title': title })
                                urlList = []

        match = re.compile('<a onclick=".+?" href="(.+?)".+?">(.+?)<', re.DOTALL).findall(html)
        urlList = []
        for url, name in match:

                host = GetDomain(url)

                #ignore unknown hosts
                if 'Unknown' in host:
                        continue
                # Resolve links if its a known Desirulez mirror
                if any(host in s for s in SITES_1) or any(host in s for s in SITES_2):
                        url = GetVideoLinks(host, url)
                        host = GetDomain(url)

                print '##################################### %s %s' %(url, name)
                # ignore .rar files
                # \.rar[(?:\.html$|\.htm$)]+
                r = re.search('\.rar[(?:\.html|\.htm)]*', url, re.IGNORECASE)
                if r:
                        print 'ignored desirulez url %s' % url
                        continue

                # find parts and build array for plalist
                print ' ------------------Name is %s----' % name
                r = re.search('Part?.([\d]+)[\s]*', name,  re.IGNORECASE)
                if r:
                        print 'found parts'
                        partNum = r.group(1)
                        if int(partNum.strip()) == 1:
                                print 'in First part'
                                if len(urlList) > 0:
                                        if showPlayAll and urlresolver.HostedMediaFile(url= urlList[0]):
                                                print 'in parts : adding previous parts %d' % len(urlList)
                                                title =  GetDomain(urlList[0]) + ' : Play All ' + str(len(urlList)) + ' Parts'
                                                addon.add_directory({'mode': 'PlayVideo', 'urlList': urlList, 'listitem': listitem}, {'title': title })
                                urlList = []
                        urlList.append(url)
                        if showAllParts and urlresolver.HostedMediaFile(url= url):
                                title =  GetDomain(url) + ' : Part ' + partNum
                                addon.add_directory({'mode': 'PlayVideo', 'urlList': [ url ], 'listitem': listitem}, {'title': title}) 
                        continue
                else:
                        if len(urlList) > 0:
                                if showPlayAll and urlresolver.HostedMediaFile(url= urlList[0]):
                                        print 'in single : adding previous parts %d' % len(urlList)
                                        title =  GetDomain(urlList[0]) + ' : Play All ' + str(len(urlList)) + ' Parts'
                                        addon.add_directory({'mode': 'PlayVideo', 'urlList': urlList, 'listitem': listitem}, {'title': title })
                        print 'single file link'
                        # if its a single link just build array of just that link
                        urlList = []
                        urlList.append(url)
                
                        if urlresolver.HostedMediaFile(url= urlList[0]):
                                host = host + ' : Single link'
                                addon.add_directory({'mode': 'PlayVideo', 'urlList': urlList, 'listitem': listitem}, {'title':  host})
                                urlList = []

        if len(urlList) > 0:
                if showPlayAll and urlresolver.HostedMediaFile(url= urlList[0]):
                        title =  GetDomain(urlList[0]) + ' : Play All ' + str(len(urlList)) + ' Parts'
                        addon.add_directory({'mode': 'PlayVideo', 'urlList': urlList, 'listitem': listitem}, {'title': title })
        
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def SortUrlList(urlList):
        print 'In SortUrlList'
        retList = [''] * len(urlList)
        for url in urlList:
                partNum = re.search('\.[0]+([\d]+)[\.]*[(?:html|htm)]*', url, re.IGNORECASE).group(1)
                retList[int(partNum) - 1] = url
        print retList
        return retList

def GetVideoLinks(host, url):
        if any(host in s for s in SITES_1):
                links = re.compile('iframe.+?src="(.+?)"', re.IGNORECASE).findall(net.http_GET(url).content)
                if len(links):
                        return links[0]
        if any(host in s for s in SITES_2):
                links = re.compile('object.+?src="(.+?)"').findall(net.http_GET(url).content)
                if len(links):
                        return links[0]
        #print 'ignored desirulez url %s' % url
        return url

def GetMirroriLinks(url):
        html = net.http_GET(url).content
        match = re.compile('<li id=".+?".+?href="(.+?)"').findall(html)
        return match

def GetMultiup(url):
        html = net.http_GET(url).content
        form_values = {}
        for i in re.finditer('<input type="hidden" name="(.+?)" value="(.+?)"', html):
            form_values[i.group(1)] = i.group(2)
        r = re.search('What is the result of ([\d]+) \+ ([\d]+)', html)
        if not r:
                print 'could not find security code'
                return []
        form_values["data[Fichier][security_code]"] = str(int(r.group(1)) + int(r.group(2)))
        html = net.http_POST(url, form_data=form_values).content
        match = re.compile('href="(.+?)">Download').findall(html)
        return match


def PlayVideo(urlList, listitem):
        print '************************************* in PlayVideo'
        print urlList
        
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	playlist.clear()
	urlList = map(str, urlList[1:-1].split(','))
	try:
                for url in urlList:
                        url = url.replace('\\r', '').replace("u'", "").replace("'", "").strip()
                        print 'url is %s' % url
                        playlist.add(url= urlresolver.HostedMediaFile(url).resolve())
                xbmc.Player().play(playlist)
        except:
                print 'error while trying to PlayVideo'

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

def MainMenu():  #homescreen

        addon.add_directory({'mode': 'HindiMenu'}, {'title': 'Hindi Movies'})       
        addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/tamil-movies', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Tamil Movies'})
        addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/telugu-movies', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Telugu Movies'})
        addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/malayalam', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Malayalam Movies'})
        addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/bengali-movies', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Bengali Movies'})
        addon.add_directory({'mode': 'GetSearchQuery'},  {'title':  'Search'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def HindiMenu():
        #addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/first-day-first-show-reviews/', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi First Day First Show'})
        addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/latest-exclusive-movie-hq', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi Latest'})
        addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/high-definition', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi HD Movies'})
        addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/dvd-rip', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi DVD Rips'})
        addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/dvd9-dvd5', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi DVD9'})
        addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/pdvd-rip', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi PDVD Rips'})
        addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/cam-rips', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi CAM Rips'})
        
        #addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/bluray-dvd-english-subs-online', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi Bluray'})
        #addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/cam-rips', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi CAM Rips'})
        #addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/pdvd-rip', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi PDVD Rips'})
        #addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/cam-rips', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi CAM Rips'})
        #addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/cam-rips', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi CAM Rips'})
        #addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + '/cam-rips', 'startPage': '1', 'numOfPages': '1'}, {'title': 'Hindi CAM Rips'})
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
        url = 'http://www.google.com/search?q=site:desirulez.net ' + query
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
	PlayVideo(urlList, listitem)	
elif mode == 'ResolverSettings':
        urlresolver.display_settings()
elif mode == 'HindiMenu':
        HindiMenu()
