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

addon_id = 'plugin.video.yourtvseries'
plugin = xbmcaddon.Addon(id=addon_id)

DB = os.path.join(xbmc.translatePath("special://database"), 'yourtvseries.db')
BASE_URL = 'http://www.yourtvseri.es'
AZ_DIRECTORIES = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y', 'Z']
GENRES = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 
          'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy', 
          'History', 'Horror', 'Music', 'Musical', 
          'Mystery', 'Romance', 'Sci-Fi', 'Short', 'Sport', 
          'Thriller', 'War', 'Western']
net = Net()
addon = Addon('plugin.video.yourtvseries', sys.argv)

hdVideo = True

if plugin.getSetting('HD') == 'false':
        hdVideo = False

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
img = addon.queries.get('img', None)
page = addon.queries.get('page', None)
episodes = addon.queries.get('episodes', None)
query = addon.queries.get('query', None)


def initDatabase():
	print "Building yourtvseries Database"
	if ( not os.path.isdir( os.path.dirname(
                ) ) ):
		os.makedirs( os.path.dirname( DB ) )
	db = sqlite.connect( DB )
	cursor = db.cursor()
	cursor.execute('CREATE TABLE IF NOT EXISTS seasons (season UNIQUE, contents);')
	cursor.execute('CREATE TABLE IF NOT EXISTS favorites (type, name, url, img);')
	db.commit()
	db.close()

def SaveFav(type, name, url, img, year):
   if type != 'tv': type = 'movie'
   db = sqlite.connect( DB )
   cursor = db.cursor()
   statement  = 'INSERT INTO favorites (type, name, url, year) VALUES (?,?,?,?)'
   try: 
      cursor.execute(statement, (type, urllib.unquote_plus(name.decode('utf-8')), url, year))
      builtin = 'XBMC.Notification(Save Favorite,Added to Favorites,2000)'
      xbmc.executebuiltin(builtin)
   except sqlite.IntegrityError: 
      builtin = 'XBMC.Notification(Save Favorite,Item already in Favorites,2000)'
      xbmc.executebuiltin(builtin)
   db.commit()
   db.close()

def GetTitles(section, url, episode = False): # Get Movie Titles
        print 'yourtvseries get Movie Titles Menu %s' % url
        html = net.http_GET(url).content
        #match = re.compile('title="Watch online: (.+?)".+?href="(.+?)".+?src="(.+?)".+?span title="(.+?)"', re.MULTILINE | re.DOTALL | re.IGNORECASE).findall(html)
        match = re.compile('title="Watch online: (.+?)".+?href="(.+?)".+?src="(.+?)"', re.DOTALL).findall(html)
        for name, url, img in match:
                #name = name + '  ( ' +  rating + ' )'
                if section == 'tv-shows' and episode == False:
                        addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url, 'img': BASE_URL + img }, {'title':  name}, img=BASE_URL + img)
                else: 
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': BASE_URL + url}, {'title':  name}, img=BASE_URL + img)
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetLinks(url): # Get TV Links
        print 'In GetLinks %s' % url
        html = net.http_GET(url).content
        html = html.encode('utf-8')
        r  = re.findall('_video_source" href="(.+?)"', html)
        if len(r) <= 1:
                print 'could not obtain video'
                return
        if hdVideo:
                qual = len(r) - 2
        else:
                qual = 0
        url = r[qual]
        url = url.replace('amp;', '')
        print 'first url is %s' % url
        orig_html = net.http_GET(url).content
        match = re.search('<iframe src="(.+?)"', orig_html)
        if not match:
                print 'could not obtain video'
                return
        url = match.group(1)
        print url
        html = net.http_GET(url).content
        match = re.search('vtag=(.+?)&.+?thumb=(.+?)video', html)
        if not match:
                print 'could not obtain video'
                return
        qual = re.search('hd=(.)', url)
        quality = '.flv'
        if qual is not None:
                print qual.group(1)
                if qual.group(1) == '1':
                        quality = '.360.mp4'
                elif qual.group(1) == '2':
                        quality = '.480.mp4'
                elif qual.group(1) == '3':
                        quality = '.720.mp4'
        stream_url = match.group(2) + 'video/' + match.group(1) + quality
        print stream_url
	listitem = GetMediaInfo(orig_html)
	xbmc.Player().play(stream_url, listitem)

def GetMediaInfo(html):
        print '----------------- in GetMediaInfo'
        listitem = xbmcgui.ListItem()
        match = re.search('<title>Watch (.+?) Season (\d\d) Episode (\d\d) ', html, re.DOTALL)
        print match
        if match:
                s = match.group(2)
                e = match.group(3)
                if s[0] == '0':
                        season = s[1]
                else:
                        season = s
                if e[0] == '0':
                        episode = e[1]
                else:
                        episode = e
                print match.group(1) + ' : ' + season + ' : ' + episode
                listitem.setInfo('video', {'TVShowTitle': match.group(1), 'Season': int(season), 'Episode': int(episode) } )
        return listitem

def MainMenu():  #homescreen
        addon.add_directory({'mode': 'BrowseAll'}, {'title':  'All Shows'})
	addon.add_directory({'mode': 'BrowseLatest'}, {'title':  'Latest Episodes'})
	addon.add_directory({'mode': 'GetSearchQuery'}, {'title':  'Search'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        

def BrowseAll(): 
	print 'Browse All screen'
        html = net.http_GET(BASE_URL).content
        match = re.compile('cat-item.+?href="(.+?)".+?>(.+?)<', re.DOTALL).findall(html)
        
        for url, title in match:
                print '%s : %s' %(title, url)
                addon.add_directory({'mode': 'GetSeasons', 'url': url}, {'title':  title})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def BrowseLatest():
	print 'Browse Latest screen'
        html = net.http_GET(BASE_URL + '/newest/').content
        episodes = re.compile('wrap" href="(.+?)".+?data-src="(.+?)".+?b>(.+?)<.+?strong>(.+?)<.+?translate">(.+?)<', re.DOTALL).findall(html)
        for epurl, epimg, title, epnum, eptitle in episodes:
                title = title.strip() + ' ' + epnum.strip() + ' ' + eptitle.encode('utf8').strip()
                addon.add_directory({'mode': 'GetLinks', 'url': epurl}, {'title':  ShrinkTitle(title)}, img= epimg)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def ShrinkTitle(title):
        title = re.sub('Season ', 'S', title)
        title = re.sub(' Episode ', 'xE', title)
        return title

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
        url = BASE_URL + '/?s='  + query
        html = net.http_GET(url).content
        results_start = re.search('series-found', html)
        html = html[results_start.end():]
        results_end = re.search('</a></li></ul></div></div>', html)
        html = html[:results_end.start()]
        match = re.compile('href="(.+?)".+?>(.+?)<').findall(html)
        for url, title in match:
                if '/series/' in url:
                        addon.add_directory({'mode': 'GetSeasons', 'url': url}, {'title':  title})
                else:
                        addon.add_directory({'mode': 'GetLinks', 'url': url}, {'title':  ShrinkTitle(title)})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetSeasons(url):
        print 'In GetSeasons %s' % url
      	xbmcplugin.setContent( int( sys.argv[1] ), 'seasons' )
	print 'Seasons for TV Show %s' % url
        html = net.http_GET(url).content
        img = ''
        match = re.search('<img itemprop.+?src="(.+?)"', html)
        if match:
                img = match.group(1)
	shows = re.compile('fwb fsxxl mtl">(.+?)<(.+?)</div></div><div class=', re.DOTALL).findall(html)   
	if shows:
                for season_name, episodes in shows:
                        episodes = episodes.encode('utf8')
                        addon.add_directory({'mode': 'GetEpisodes', 'episodes': episodes}, {'title':  season_name.strip()}, img= img)
		xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetEpisodes(episodes): 
	xbmcplugin.setContent( int( sys.argv[1] ), 'episodes' )
	episodes = re.compile('href="(.+?)".+?ep_num">(.+?)<.+?title">(.+?)<', re.DOTALL).findall(episodes) 
	for epurl, epnum, title in episodes:
                title = epnum.strip() + ' : ' + title.encode('utf8').strip()
                addon.add_directory({'mode': 'GetLinks', 'url': epurl}, {'title':  title})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
          

if mode == 'main': 
	MainMenu()
elif mode == 'BrowseAll': 
	BrowseAll()
elif mode == 'BrowseLatest': 
	BrowseLatest()
elif mode == 'GetTitles': 
	GetTitles(url)
elif mode == 'GetLinks':
	GetLinks(url)
elif mode == 'GetSeasons':
	GetSeasons(url)
elif mode == 'GetEpisodes':
	GetEpisodes(episodes)
elif mode == 'GetSearchQuery':
	GetSearchQuery()
elif mode == 'Search':
	Search(query)

