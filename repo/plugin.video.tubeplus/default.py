import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string, sys, os
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net

try:
	from sqlite3 import dbapi2 as sqlite
	print "Loading sqlite3 as DB engine"
except:
	from pysqlite2 import dbapi2 as sqlite
	print "Loading pysqlite2 as DB engine"


DB = os.path.join(xbmc.translatePath("special://database"), 'tubeplus.db')
BASE_URL = 'http://www.tubeplus.me'
AZ_DIRECTORIES = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y', 'Z']
GENRES = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 
          'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy', 
          'History', 'Horror', 'Music', 'Musical', 
          'Mystery', 'Romance', 'Sci-Fi', 'Short', 'Sport', 
          'Thriller', 'War', 'Western']
net = Net()
addon = Addon('plugin.video.tubeplus', sys.argv)

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
section = addon.queries.get('section', None)
img = addon.queries.get('img', None)
genre = addon.queries.get('genre', None)
letter = addon.queries.get('letter', None)
page = addon.queries.get('page', None)
episodes = addon.queries.get('episodes', None)
query = addon.queries.get('query', None)


def initDatabase():
	print "Building tubeplus Database"
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
        print 'Tubeplus get Movie Titles Menu %s' % url
        html = net.http_GET(url).content
        #match = re.compile('title="Watch online: (.+?)".+?href="(.+?)".+?src="(.+?)".+?span title="(.+?)"', re.MULTILINE | re.DOTALL | re.IGNORECASE).findall(html)
        match = re.compile('title="Watch online: (.+?)".+?href="(.+?)".+?src="(.+?)"').findall(html)
        for name, url, img in match:
                #name = name + '  ( ' +  rating + ' )'
                if section == 'tv-shows' and episode == False:
                        addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url, 'img': BASE_URL + img }, {'title':  name}, img=BASE_URL + img)
                else: 
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': BASE_URL + url}, {'title':  name}, img=BASE_URL + img)
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetLinks(section, url): # Get Movie Links
        print 'In GetLinks'
        html = net.http_GET(url).content
        sources = []
        if 'Try links found on Google' in html:
                match = re.compile('<a class="glink".+?">(.+?)<').findall(html)
                if len(match) > 0:
                        count = 1
                        for url in match:
                                name = str(count) + ". " + GetDomain(url)
                                hosted_media = urlresolver.HostedMediaFile(url=url, title=name)
                                sources.append(hosted_media)
                                count = count + 1
        else:
                #match = re.compile('<a class="none" href="(.+?)".+?\[(.+?)\].+? - (.+?) -.+?<b>(.+?) ', re.MULTILINE | re.DOTALL | re.IGNORECASE).findall(html)
                if section == 'tv-shows':
                        match = re.compile('<a class="none" href="(.+?)".+?<span>Host: </span>(.+?)\n', re.MULTILINE | re.DOTALL | re.IGNORECASE).findall(html)
                        if len(match) > 0:
                                count = 1
                                for url, host in match:
                                        name = str(count) + ". " + host
                                        hosted_media = urlresolver.HostedMediaFile(url=url, title=name)
                                        sources.append(hosted_media)
                                        count = count + 1 
                else:
                        match = re.compile('<a class="none" href="(.+?)".+?\[(.+?)\].+?<span>Host: </span>(.+?)\n', re.MULTILINE | re.DOTALL | re.IGNORECASE).findall(html)
                        if len(match) > 0:
                                count = 1
                                for url, quality, host in match:
                                        name = str(count) + ". " + host + ' - ' + quality
                                        hosted_media = urlresolver.HostedMediaFile(url=url, title=name)
                                        sources.append(hosted_media)
                                        count = count + 1
	source = urlresolver.choose_source(sources)
	if source:
                stream_url = source.resolve()
	else:
                return
	listitem = xbmcgui.ListItem()
	if  ( section == 'tv-shows'):
                match = re.search('<h1>(.+?)  - SEASON: (.+?) EPISODE: (.+?) ', html)
                print match.group(1)
                print match.group(2)
                print match.group(3)
                listitem.setInfo('video', {'TVShowTitle': match.group(1), 'Season': int(match.group(2)), 'Episode': int(match.group(3)) } )
        else:
                match = re.search('<h1>(.+?) \((.+?)\)', html)
                listitem.setInfo('video', {'Title': match.group(1), 'Year': int(match.group(2))} )
                
	xbmc.Player().play(stream_url, listitem)

def GetDomain(url):
        tmp = re.compile('//(.+?)/').findall(url)
        domain = 'Unknown'
        if len(tmp) > 0 :
            domain = tmp[0].replace('www.', '')
        return domain

def MainMenu():  #homescreen
        addon.add_directory({'mode': 'LoadCategories', 'section': 'movies'}, {'title':  'Movies'})
	addon.add_directory({'mode': 'LoadCategories', 'section': 'tv-shows'}, {'title':  'TV Shows'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        
def LoadCategories(section): #Categories
         
        addon.add_directory({'mode': 'BrowseAtoZ', 'section': section}, {'title':  'A-Z'})
	addon.add_directory({'mode': 'BrowseGenre', 'section': section}, {'title':  'Genres'})
	addon.add_directory({'mode': 'BrowseLatest', 'section': section}, {'title':  'Latest'})
	#addon.add_directory({'mode': 'GetTitles', 'section': section}, {'title':  'Favorites'})
	addon.add_directory({'mode': 'GetSearchQuery', 'section': section}, {'title':  'Search'})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def BrowseAtoZ(section=None, genre=None): 
	print 'Browse by alphabet screen'
	addon.add_directory({'mode': 'GetResults', 'section': section, 'genre': genre, 'letter': '-'}, {'title':  '#123'})
	for character in AZ_DIRECTORIES:
                addon.add_directory({'mode': 'GetResults', 'section': section, 'genre': genre, 'letter': character}, {'title':  character})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def BrowseGenre(section=None, letter=None): 
	print 'Browse by genres screen'
	for g in GENRES:
                addon.add_directory({'mode': 'GetResults', 'section': section, 'genre': g}, {'title':  g})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetSearchQuery(section):
	last_search = addon.load_data('search')
	if not last_search: last_search = ''
	keyboard = xbmc.Keyboard()
	if section == 'tv-shows': keyboard.setHeading('Search TV Shows')
	else: keyboard.setHeading('Search Movies')
	keyboard.setDefault(last_search)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
                query = keyboard.getText()
                addon.save_data('search',query)
                Search(section, query)
	else:
                return

def Search(section, query):
        url = BASE_URL + '/search/' + section + '/'  + query  + '/'
        GetTitles(section, url)


def GetResults(section=None, genre=None, letter=None, page=None): 
	print 'Filtered results for Section: %s Genre: %s Letter: %s Page: %s' % \
			(section, genre, letter, page)
	if section == 'tv-shows':	xbmcplugin.setContent( int( sys.argv[1] ), 'tvshows' )
	else: xbmcplugin.setContent( int( sys.argv[1] ), 'movies' )

        suffix = '/' + genre + '/'
        
        if not letter:
                suffix = suffix + 'ALL/'
        else:
                suffix = suffix + letter + '/'
                
	url = BASE_URL + '/browse/' + section + suffix
	print url
        GetTitles(section, url)


def GetSeasons(section, url, img):
      	xbmcplugin.setContent( int( sys.argv[1] ), 'seasons' )
	print 'Seasons for TV Show %s' % url
        html = net.http_GET(url).content
	shows = re.compile("javascript:show_season.+?'>(.+?)<(.+?)</span>", re.DOTALL).findall(html)   
	if not shows: print 'couldn\'t find seasons'
	else:
		for season_name, episodes in shows:
                        episodes = episodes.encode('utf8')
                        addon.add_directory({'mode': 'GetEpisodes', 'section': section, 'img': img, 'episodes': episodes}, {'title':  season_name}, img= img)
		xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetEpisodes(section, img, episodes): 
	xbmcplugin.setContent( int( sys.argv[1] ), 'episodes' )
	r = 'href=(.+?)">(.+?)<'
	episodes = re.compile(r, re.DOTALL).findall(episodes) 
	for epurl, title in episodes:
		print '%s @ %s' %(title, epurl)
                addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': BASE_URL + epurl}, {'title':  title.decode('utf8')}, img=BASE_URL + img)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
          

if mode == 'main': 
	MainMenu()
elif mode == 'LoadCategories': 
	LoadCategories(section)
elif mode == 'BrowseAtoZ': 
	BrowseAtoZ(section)
elif mode == 'BrowseGenre': 
	BrowseGenre(section)
elif mode == 'BrowseLatest': 
	GetTitles(section, BASE_URL + '/browse/'+ section +'/Last/ALL/', episode = True)
elif mode == 'GetResults': 
	GetResults(section, genre, letter, page)
elif mode == 'GetTitles': 
	GetTitles(url)
elif mode == 'GetLinks':
	GetLinks(section, url)
elif mode == 'GetSeasons':
	GetSeasons(section, url, img)
elif mode == 'GetEpisodes':
	GetEpisodes(section, img, episodes)
elif mode == 'GetSearchQuery':
	GetSearchQuery(section)
elif mode == 'Search':
	Search(section, query)
elif mode == 'ResolverSettings':
        urlresolver.display_settings()
