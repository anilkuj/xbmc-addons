import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string, sys, os
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
import datetime as dt
import HTMLParser


try:
	from sqlite3 import dbapi2 as sqlite
	print "Loading sqlite3 as DB engine"
except:
	from pysqlite2 import dbapi2 as sqlite
	print "Loading pysqlite2 as DB engine"

addon_id = 'plugin.video.tvlinks'
plugin = xbmcaddon.Addon(id=addon_id)

DB = os.path.join(xbmc.translatePath("special://database"), 'tvlinks.db')
BASE_URL = 'http://www.tv-links.eu'
AZ_DIRECTORIES = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y', 'Z']
GENRES = ['Action', 'Adventure', 'Animation', 'Biography', 'Celebrities', 'Comedy', 'Cooking/Food',
          'Crime', 'Design/Decorating', 'Documentary', 'Drama', 'Educational', 'Family', 'Fantasy', 'Fashion/Make-up', 'Foreign', 'Game-Show',
          'History', 'Horror', 'Music', 'Musical', 
          'Mystery', 'News', 'Pets/Animals', 'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 
          'Talk-Show', 'Thriller', 'War', 'Western']
addon = Addon('plugin.video.tvlinks', sys.argv)
DATA_PATH = os.path.join(xbmc.translatePath('special://profile/addon_data/plugin.video.tvlinks'), '')
cookie_jar = os.path.join(DATA_PATH, "cookiejar.lwp")
net = Net(cookie_file= cookie_jar)
dialog = xbmcgui.Dialog()
pages = '2'


try:
        os.makedirs(os.path.dirname(cookie_jar))
except OSError:
        pass

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
section = addon.queries.get('section', None)
img = addon.queries.get('img', None)
genre = addon.queries.get('genre', None)
letter = addon.queries.get('letter', None)
page = addon.queries.get('page', None)
episodes = addon.queries.get('episodes', None)
showTitle = addon.queries.get('showTitle', None)
seasonNum = addon.queries.get('seasonNum', None)
episodeNum = addon.queries.get('episodeNum', None)
query = addon.queries.get('query', None)
listitem = addon.queries.get('listitem', None)
startPage = addon.queries.get('startPage', None)
numOfPages = addon.queries.get('numOfPages', None)
count = addon.queries.get('count', None)


def initDatabase():
	print "Building tvlinks Database"
	if ( not os.path.isdir( os.path.dirname(
                ) ) ):
		os.makedirs( os.path.dirname( DB ) )
	db = sqlite.connect( DB )
	cursor = db.cursor()
	cursor.execute('CREATE TABLE IF NOT EXISTS seasons (season UNIQUE, contents);')
	cursor.execute('CREATE TABLE IF NOT EXISTS favorites (type, name, url, img);')
	db.commit()
	db.close()

def SaveFav(section, url, name=None, year=None, imdbid=None):
        match = re.search(' class="dark">[A-Z#]<.+?href=".+?".*?>(.+?) \((.+?)\)<.+?imdb.com.title.(.+?)\/', html)
        name, year, imdbid = match.groups()
        db = sqlite.connect( DB )
        cursor = db.cursor()
        statement  = 'INSERT INTO favorites (section, name, url, year, imdbid) VALUES (?,?,?,?,?)'
        try: 
                cursor.execute(statement, (section, urllib.unquote_plus(name.decode('utf-8')), url, year, imdbid))
                builtin = 'XBMC.Notification(Save Favorite,Added to Favorites,2000)'
                xbmc.executebuiltin(builtin)
        except sqlite.IntegrityError: 
                builtin = 'XBMC.Notification(Save Favorite,Item already in Favorites,2000)'
                xbmc.executebuiltin(builtin)
        db.commit()
        db.close()

def GetTitles(section, url, episode = False): # Get Movie Titles
        print 'tvlinks get Movie Titles Menu %s' % url
        html = net.http_GET(url).content
        match = re.compile('<li> <a href="(.+?)" class="list cfix"> <span class="c1">(.+?)<').findall(html)
        for url, name in match:
                #name = name + '  ( ' +  rating + ' )'
                if section == 'tv':
                        addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url}, {'title':  name})
                else: 
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': BASE_URL + url, 'startPage': '1', 'numOfPages': pages}, {'title':  name}, img=BASE_URL + img)
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetLinks(section, url, showTitle=None, seasonNum=None, episodeNum=None, startPage= '1', numOfPages= '1', count= '1'): # Get TV/Movie Links
        html = net.http_GET(url).content
        if showTitle is None:
                match = re.search('<input type="text" value="(.+?): Season (.+?) Episode (.+?) ', html)
                showTitle, seasonNum, episodeNum = match.groups()
       
        listitem = xbmcgui.ListItem()
        listitem.setInfo('video', {'TVShowTitle': showTitle, 'Season': int(seasonNum), 'Episode': int(episodeNum) } )

        pageUrl = url
        if startPage > '1':
                pageUrl = url + '?apg=' + startPage
        html = net.http_GET(pageUrl).content
        start = int(startPage)
        end = start + int(numOfPages)
        last = GetLastPage(html)
        print str(start) + ' : ' + str(end) + ' : ' + str(last)
        if count:
                count = int(count)
        else:
                count = 1
        for page in range( start, min(last, end)):
                if ( page != start):
                        pageUrl = url + '?apg=' + str(page)
                        html = net.http_GET(pageUrl).content
                print pageUrl
                match = re.compile('return frameLink.\'(.+?)\'.+?Play full video.+?bold">(.+?)<.+?green">(.+?) voted').findall(html)
                for gatewayId, host, votes in match:
                        name = str(count) + ". " + host + " " + votes
                        if urlresolver.HostedMediaFile(host=host, media_id='xxx'):
                                addon.add_directory({'mode': 'PlayVideo', 'section': section, 'url': gatewayId, 'listitem': listitem}, {'title':  name})
                        count = count + 1
       	if end < last:
                addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': url, 'showTitle': showTitle, 'seasonNum': seasonNum,
                                     'episodeNum': episodeNum, 'startPage': str(end), 'numOfPages': numOfPages, 'count': str(count)}, {'title':  'Next..'})
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))
       	

def GetLastPage(html):
        lastPage = 2
        match = re.compile("'?apg=([\d]+)'").findall(html)
        if match:
                lastPage = int(match[len(match) - 2])
        print 'total pages %s ' % lastPage
        return lastPage
        

def PlayVideo(section, gatewayId, listitem):
        url = 'http://www.tv-links.eu/gateway.php?data='+gatewayId
        res = net.http_GET(url)
        finalurl = res.get_url()
        print 'final url is %s' % finalurl
        stream_url = urlresolver.HostedMediaFile(finalurl).resolve()
        print 'stream url is %s' % stream_url
        xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(stream_url, listitem)


def MainMenu():  #homescreen
        #addon.add_directory({'mode': 'LoadCategories', 'section': 'movies'}, {'title':  'Movies'})
	#addon.add_directory({'mode': 'LoadCategories', 'section': 'tv-shows'}, {'title':  'TV Shows'})
	addon.add_directory({'mode': 'BrowseLatest', 'section': 'tv'}, {'title':  'Latest'})
	addon.add_directory({'mode': 'BrowsePopular', 'section': 'tv'}, {'title':  'Popular'})
        addon.add_directory({'mode': 'BrowseAtoZ', 'section': 'tv'}, {'title':  'A-Z'})
	addon.add_directory({'mode': 'BrowseGenre', 'section': 'tv'}, {'title':  'Genres'})
	if Login():
                addon.add_directory({'mode': 'Favorites', 'section': 'tv'}, {'title':  'Favorites'})
	addon.add_directory({'mode': 'GetSearchQuery', 'section': 'tv'}, {'title':  'Search'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        
#def LoadCategories(section): #Categories
         
        #addon.add_directory({'mode': 'BrowseAtoZ', 'section': section}, {'title':  'A-Z'})
	#addon.add_directory({'mode': 'BrowseGenre', 'section': section}, {'title':  'Genres'})
	#addon.add_directory({'mode': 'GetTitles', 'section': section}, {'title':  'Favorites'})
	#addon.add_directory({'mode': 'Search', 'section': section}, {'title':  'Search'})
	#xbmcplugin.endOfDirectory(int(sys.argv[1]))

def BrowseAtoZ(section=None, genre=None): 
	print 'Browse by alphabet screen'
	addon.add_directory({'mode': 'GetResults', 'section': section, 'genre': genre, 'letter': '0-9'}, {'title':  '#'})
	for character in AZ_DIRECTORIES:
                addon.add_directory({'mode': 'GetResults', 'section': section, 'genre': genre, 'letter': character}, {'title':  character})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def BrowseLatest(section=None):
        print 'Browse Latest screen'
        d = dt.datetime.now() - dt.timedelta( days = 1 )
        latest = '%d/%d/%d' %(d.month, d.day, d.year)
        url = BASE_URL + '/schedule.html?date=' + latest
        html = net.http_GET(url).content
        match = re.compile('width="45" alt="(.+?)".+?c2 brd_r_dot"><a href="(.+?)">Season (.+?), Episode (.+?)<.+?em><a.+?>(.+?)<', re.MULTILINE | re.DOTALL).findall(html)
        for title, url, seasonNum, episodeNum, episodeTitle in match:
                name = title + ' S' +  seasonNum + 'xE' + episodeNum + ' : ' + episodeTitle
                url = BASE_URL + url + 'video-results/'
                addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': url, 'startPage': '1', 'numOfPages': pages}, {'title':  name})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
                

def BrowsePopular(section=None):
        print 'Browse Popular screen'
        url = BASE_URL
        html = net.http_GET(url).content
        match = re.compile('<li> <a href="(.+?)".+?bigger">(.+?)<').findall(html)
        if section == 'tv':
                for url, name in match:
                        addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url}, {'title':  name})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
                

def BrowseGenre(section=None, year=None): 
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
		Search(query)
	else:
                return

def Search(query):
        url = BASE_URL + '/_search/?s='  + query
        html = net.http_GET(url).content
        match = re.compile('<li> <a href="(.+?)".+?src="(.+?)".+?bold">(.+?)<.+?Category.+?> (.+?),').findall(html)
        for url, img, name, cat in match:
                if  'TV' in cat:
                        addon.add_directory({'mode': 'GetSeasons', 'section': 'tv', 'url': BASE_URL + url}, {'title':  name}, img= img)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetResults(section=None, genre=None, letter=None, page=None): 
	print 'Filtered results for Section: %s Genre: %s Letter: %s Page: %s' % \
			(section, genre, letter, page)
	if section == 'tv':	xbmcplugin.setContent( int( sys.argv[1] ), 'tvshows' )
	else: xbmcplugin.setContent( int( sys.argv[1] ), 'movies' )

        url = BASE_URL
	if section == 'tv':
                url = url +'/tv-shows/'

        if letter == None:
                url = url + genre + '_0'
        else:
                url = url + letter + '.html'
        GetTitles(section, url)


def GetSeasons(section, url):
      	xbmcplugin.setContent( int( sys.argv[1] ), 'seasons' )
	print 'Seasons for TV Show %s' % url
        html = net.http_GET(url).content
	#shows = re.compile("Season (\d+)<\/div>(.+?)<.a> <.li> <.ul>|Season (\d+) <em(.+?)<.a> <.li> <.ul>", re.DOTALL).findall(html)
        shows = re.compile("Season (\d+)<\/div>(.+?)<.a> <.li> <.ul>", re.DOTALL).findall(html)   
	if shows:
		for season_name, episodes in shows:
                        #episodes = episodes.encode('utf8')
                        season_name = 'Season ' + season_name
                        addon.add_directory({'mode': 'GetEpisodes', 'section': section, 'episodes': episodes.encode("utf-8")}, {'title':  season_name})

	shows = re.compile("Season (\d+) <em(.+?)<.a> <.li> <.ul>", re.DOTALL).findall(html)   
	if shows:
		for season_name, episodes in shows:
                        #episodes = episodes.encode('utf8')
                        season_name = 'Season ' + season_name
                        addon.add_directory({'mode': 'GetEpisodes', 'section': section, 'episodes': episodes.encode("utf-8")}, {'title':  season_name})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetEpisodes(section, episodes): 
	xbmcplugin.setContent( int( sys.argv[1] ), 'episodes' )
	r = 'href="(.+?)".+?c1">(.+?)<.+?c2">(.+?)<'
	episodes = re.compile(r, re.DOTALL).findall(episodes) 
	for epurl, epnum, eptitle in episodes:
		print '%s @ %s @ %s' %(epnum, eptitle, epurl)
		title = epnum + ' : ' + eptitle
		url = BASE_URL + epurl + 'video-results/'
                addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': url, 'startPage':'1', 'numOfPages': pages}, {'title':  title.decode("utf-8")})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
          
def Login():
        html = net.http_GET(BASE_URL).content
        user = plugin.getSetting('tvlinks-username')
        password = plugin.getSetting('tvlinks-password')
        login = plugin.getSetting('tvlinks-account')

        if   'em> ' + user + '<' in html:
                return True
        if login ==  'true':
                loginURL = "http://www.tv-links.eu/ajax.php"
                data = { 'action': '7', 'sri': '0.24217649600264657',  'username': user, 'passw': password } #need a random number here ?
                html = net.http_POST(loginURL, data).content
                print html
                net.save_cookies(cookie_jar)
                net.set_cookies(cookie_jar)
                html = net.http_GET(BASE_URL).content
                if   'em> ' + user + '<' in html:
                        return True
                else:
                        dialog.ok("Tvlinks", "Invalid username or password")
                        return False
                return True
        else:
                return False

def Favorites(section):
        print 'in Favorites'
  	html = net.http_GET(BASE_URL + "/myaccount.html?zone=favorites" ).content
  	print html
        numOfFav = re.search( 'class="a_right"><b>(.+?)</', html).group(1)
        print numOfFav
        totalPages = int(numOfFav) / 12
        totalPages += 1
        if "No favorites yet" in html:
		dialog.ok("Tvlinks", "There are no favorites for this user.")
	else:
                print 'in else %d' % totalPages
                for index in range(1, totalPages + 1):
                        if index > 1:
				html = net.http_GET("http://www.tv-links.eu/myaccount.html?zone=favorites&ap=" + str(index)).content
			match = re.compile( 'img"><a href="(.+?)".+?src="(.+?)".+?alt="(.+?)"').findall(html)
			#print html
			print len(match)
                        for url, img, title in match:
                                print 'in for loop %s' %url
                                if '/tv-shows/' in url:
                                        print 'Found tv-show'
                                        addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url}, {'title':  title})
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
	BrowseLatest(section)
elif mode == 'BrowsePopular': 
	BrowsePopular(section)
elif mode == 'GetResults': 
	GetResults(section, genre, letter, page)
elif mode == 'GetTitles': 
	GetTitles(url)
elif mode == 'GetLinks':
	GetLinks(section, url, showTitle= showTitle, seasonNum= seasonNum, episodeNum= episodeNum, startPage= startPage, numOfPages= numOfPages, count= count) 
elif mode == 'GetSeasons':
	GetSeasons(section, url)
elif mode == 'GetEpisodes':
	GetEpisodes(section, episodes)
elif mode == 'GetSearchQuery':
	GetSearchQuery(section)
elif mode == 'Favorites':
	Favorites(section)
elif mode == 'Search':
	Search(query)
elif mode == 'PlayVideo':
	PlayVideo(section, url, listitem)
elif mode == 'ResolverSettings':
        urlresolver.display_settings()
