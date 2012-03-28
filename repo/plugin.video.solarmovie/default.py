import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string, sys, os
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
import HTMLParser
import unicodedata

try:
	from sqlite3 import dbapi2 as sqlite
	print "Loading sqlite3 as DB engine"
except:
	from pysqlite2 import dbapi2 as sqlite
	print "Loading pysqlite2 as DB engine"

DB = os.path.join(xbmc.translatePath("special://database"), 'solarmovie.db')
BASE_URL = 'http://www.solarmovie.eu'
net = Net()
addon = Addon('plugin.video.solarmovie', sys.argv)

GENRES = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 
          'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy', 'Film-Noir', 'Game-Show'
          'History', 'Horror', 'Music', 'Musical', 
          'Mystery', 'News', 'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 'Talk-Show'
          'Thriller', 'War', 'Western']

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
section = addon.queries.get('section', None)
img = addon.queries.get('img', None)
genre = addon.queries.get('genre', None)
year = addon.queries.get('year', None)
letter = addon.queries.get('letter', None)
page = addon.queries.get('page', None)
episodes = addon.queries.get('episodes', None)
listitem = addon.queries.get('listitem', None)
query = addon.queries.get('query', None)



def initDatabase():
	print "Building solarmovie Database"
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

def unicode_urlencode(value): 
	if isinstance(value, unicode): 
		return urllib.quote(value.encode("utf-8"))
	else: 
		return urllib.quote(value)


def GetTitles(section, url, html= None, episode = False): # Get Titles
        print 'Solarmovie get Titles Menu %s \n' % url
        if html is None :
                html = net.http_GET(url).content
        match = re.compile('class="coverImage" title="(.+?)".+?href="(.+?)".+?src="(.+?)"', re.MULTILINE | re.IGNORECASE | re.DOTALL).findall(html)
        for name, url, img in match:
                name = HTMLParser.HTMLParser().unescape(name)
                if section == 'tv' and episode == False:
                        addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url, 'img': img }, {'title':  name}, img= img)
                else:
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': BASE_URL + url}, {'title':  name}, img= img)
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetLinks(section, url): # Get Movie Links
        print 'In GetLinks %s' % url
        html = net.http_GET(url).content
        sources = []
	listitem = xbmcgui.ListItem()
	if  ( section == 'tv'):
                match = re.search('bradcramp.+?href=".+?>(.+?)<.+?href=".+?>        Season (.+?) .+?[&nbsp;]+Episode (.+?)<', html, re.MULTILINE | re.IGNORECASE | re.DOTALL)
                listitem.setInfo('video', {'TVShowTitle': match.group(1), 'Season': int(match.group(2)), 'Episode': int(match.group(3)) } )
        else:
                match = re.search('float:left;">(.+?)<em.+?html">[\n]*(.+?)</a>', html, re.MULTILINE | re.IGNORECASE | re.DOTALL)
                listitem.setInfo('video', {'Title': match.group(1).strip(), 'Year': int(match.group(2).strip())} )
                
        match = re.compile('<tr id=.+?href="(.+?)">(.+?)<.+?votes" \/>(.+?)<.+?class="qualityCell">(.+?)<', re.MULTILINE | re.DOTALL | re.IGNORECASE).findall(html)
        print ' length of match is %d' % len(match)
        if len(match) > 0:
                count = 1
                for url, host, vote, quality in match:
                        votePer = ""
                        if '%' in vote:
                              votePer =   ' - ' + vote.strip()
                        name = str(count) + ". " + host + votePer +  ' - ' + quality.strip()
                        if urlresolver.HostedMediaFile(host=host, media_id='xxx'):
                                addon.add_directory({'mode': 'PlayVideo', 'url': url, 'listitem': listitem}, {'title':  name})
                                count = count + 1 
                xbmcplugin.endOfDirectory(int(sys.argv[1]))
	else:
                return
           

def PlayVideo(url, listitem):
        print 'in PlayVideo'
        match = re.search( '/.+?/.+?/(.+?)/', url)
        videoId = match.group(1)
        url = BASE_URL + '/link/play/' + videoId + '/'
        print '**************** %s' % url
        html = net.http_GET(url).content
        match = re.search( '<iframe.+?src="(.+?)"', html, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        link = match.group(1)
        link = link.replace('/embed/', '/file/')
        stream_url = urlresolver.HostedMediaFile(link).resolve()
	xbmc.Player().play(stream_url, listitem)
        
def GetDomain(url):
        tmp = re.compile('//(.+?)/').findall(url)
        domain = 'Unknown'
        if len(tmp) > 0 :
            domain = tmp[0].replace('www.', '')
        return domain

def MainMenu():  #homescreen
        print 'in main menu'
        addon.add_directory({'mode': 'LoadCategories', 'section': 'movies'}, {'title':  'Movies'})
	addon.add_directory({'mode': 'LoadCategories', 'section': 'tv'}, {'title':  'TV Shows'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        
def LoadCategories(section): #Categories

	addon.add_directory({'mode': 'BrowseLatest', 'section': section}, {'title':  'Latest'})
        addon.add_directory({'mode': 'BrowsePopular', 'section': section}, {'title':  'Popular'})
        addon.add_directory({'mode': 'BrowseYear', 'section': section}, {'title':  'Year'})
	addon.add_directory({'mode': 'BrowseGenre', 'section': section}, {'title':  'Genres'})
        #addon.add_directory({'mode': 'BrowseAtoZ', 'section': section}, {'title':  'A-Z'})
	addon.add_directory({'mode': 'GetSearchQuery', 'section': section}, {'title':  'Search'})
	#addon.add_directory({'mode': 'GetTitles', 'section': section}, {'title':  'Favorites'})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def BrowseLatest(section=None):
	print 'Browse Latest screen'
        html = net.http_GET(BASE_URL).content
        titles = ""
	if section == 'movies':
               	match1 = re.search('<div id="first1"', html)
               	match2 = re.search('<h2>Latest TVs', html)
               	titles = html[match1.end():match2.start()]
        else:
                match1 = re.search('<h2>Latest TVs', html)
               	match2 = re.search('<div id="sidebar">', html)
               	titles = html[match1.end():match2.start()]
       	GetTitles(section, "", html=titles, episode=True)


def BrowsePopular(section=None):
	print 'Browse Popular screen'
        html = net.http_GET(BASE_URL).content
        titles = ""
	if section == 'movies':
               	match1 = re.search('<div id="second1"', html)
               	match2 = re.search('<h2>Most popular TVs today', html)
               	titles = html[match1.end():match2.start()]
        else:
                match1 = re.search('<h2>Most popular TVs today', html)
               	match2 = re.search('<div id="first1"', html)
               	titles = html[match1.end():match2.start()]
       	GetTitles(section, "", html=titles)


def BrowseAtoZ(section=None, genre=None): 
	print 'Browse by alphabet screen'
	addon.add_directory({'mode': 'GetResults', 'section': section, 'genre': genre, 'letter': '-'}, {'title':  '#123'})
	for character in AZ_DIRECTORIES:
                addon.add_directory({'mode': 'GetResults', 'section': section, 'genre': genre, 'letter': character}, {'title':  character})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def BrowseYear(section=None, genre=None):
	print 'Browse by year screen'
	url = ''
##	if section == 'movies':
##                url = BASE_URL + '/years.html'
##        else:
##                url = BASE_URL + '/' + section + '/years.html'
##        html = net.http_GET(url).content
##        match = re.search('<div class="genresPage">', html, re.MULTILINE | re.DOTALL )
##        html = html[match.end():]
##        years = re.compile('href="(.+?)".+?class="tag\d+">(.+?)<', re.MULTILINE | re.DOTALL).findall(html)
##        if section == 'movies':
##                url = '/watch-movies-of-2012.html'
##                addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + url, 'section': section, 'genre': genre}, {'title':  '2012'})
##                url = '/watch-movies-of-2011.html'
##                addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + url, 'section': section, 'genre': genre}, {'title':  '2011'})
##        else:
##                url = '/tv/watch-tv-shows-2012.html'
##                addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + url, 'section': section, 'genre': genre}, {'title':  '2012'})
##                url = '/tv/watch-tv-shows-2011.html'
##                addon.add_directory({'mode': 'GetTitles', 'url': BASE_URL + url, 'section': section, 'genre': genre}, {'title':  '2011'})
        for year in range(2012, 1930, -1):
                if section == 'movies':
                        url = BASE_URL + '/watch-movies-of-' + str(year) + '.html'
                else:
                        url = BASE_URL + '/tv/watch-tv-shows-' + str(year) + '.html'
                addon.add_directory({'mode': 'GetTitles', 'url': url, 'section': section, 'genre': genre}, {'title':  str(year)})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

        
def BrowseGenre(section=None, year=None): 
	print 'Browse by genres screen'
	url = ''
	#if section == 'movies':
        #        url = BASE_URL + '/genres.html'
        #else:
        #       url = BASE_URL + '/' + section + '/genres.html'
        #html = net.http_GET(url).content
        #match = re.search('<div class="genresPage">', html, re.MULTILINE | re.DOTALL )
        #html = html[match.end():]
        #genres = re.compile('href="(.+?)".+?class="tag\d+">(.+?)<', re.MULTILINE | re.DOTALL).findall(html)
        for genre in GENRES:
                if section == 'movies':
                        url = BASE_URL + '/watch-' + genre + '-movies.html'
                else:
                        url = BASE_URL + '/tv/watch-' + genre + '-tv-shows.html'
                addon.add_directory({'mode': 'GetTitles', 'url': url, 'section': section, 'year': year}, {'title':  genre})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetSearchQuery(section):
	last_search = addon.load_data('search')
	if not last_search: last_search = ''
	keyboard = xbmc.Keyboard()
	if section == 'tv': keyboard.setHeading('Search TV Shows')
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
        cat = 'tv'
        if section == 'movies':
                cat = 'movie'
        url = BASE_URL + '/' + cat + '/search/' + query + '/'
        GetTitles(section, url)

def GetResults(section=None, genre=None, letter=None, page=None): 
	
	if section == 'tv':	xbmcplugin.setContent( int( sys.argv[1] ), 'tvshows' )
	else: xbmcplugin.setContent( int( sys.argv[1] ), 'movies' )

        suffix = '/' + genre + '/'
        
        if not letter:
                suffix = suffix + 'ALL/'
        else:
                suffix = suffix + letter + '/'
                
	url = BASE_URL + '/browse/' + section + suffix
        GetTitles(section, url)


def GetSeasons(section, url, img):
      	xbmcplugin.setContent( int( sys.argv[1] ), 'seasons' )
	print 'Seasons for TV Show'
        html = net.http_GET(url).content
        match = re.search( 'coverImage">.+?src="(.+?)"', html, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        img = match.group(1)
	shows = re.compile('<a class="behavior_trigger_season.+?id="trigger_(.+?)"(.+?)<h4>', re.DOTALL).findall(html)   
	if not shows: print 'couldn\'t find seasons'
	else:
		for season_name, episodes in shows:
                        season_name = season_name.replace( '_',  ' ')
                        addon.add_directory({'mode': 'GetEpisodes', 'section': section, 'img': img, 'episodes': episodes.encode('utf-8')}, {'title':  season_name}, img= img)
		xbmcplugin.endOfDirectory(int(sys.argv[1]))


def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', unicode(input_str))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

def GetEpisodes(section, img, episodes):
        print 'in Get Episodes'
	xbmcplugin.setContent( int( sys.argv[1] ), 'episodes' )
	episodes = re.compile('epnomber.+?href="(.+?)">(.+?)<.+?/episode-.+?/">(.+?)<.+?/episode-.+?/.+?>(.+?)<', re.IGNORECASE | re.MULTILINE | re.DOTALL).findall(episodes)
	for epurl, epnbr, title, numOfLinks in episodes:
		title = HTMLParser.HTMLParser().unescape(title)
		#title = unicode_urlencode(title)
                addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': BASE_URL + epurl}, {'title':  epnbr + ' - ' + title +  ' (' + numOfLinks.strip() + ')'}, img= img)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
          

if mode == 'main': 
	MainMenu()
elif mode == 'LoadCategories': 
	LoadCategories(section)
elif mode == 'BrowseAtoZ': 
	BrowseAtoZ(section)
elif mode == 'BrowseYear': 
	BrowseYear(section)
elif mode == 'BrowseGenre': 
	BrowseGenre(section)
elif mode == 'BrowseLatest': 
	BrowseLatest(section)
elif mode == 'BrowsePopular': 
	BrowsePopular(section)
elif mode == 'GetResults': 
	GetResults(section, genre, letter, page)
elif mode == 'GetTitles': 
	GetTitles(section, url)
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
elif mode == 'PlayVideo':
	PlayVideo(url, listitem)
elif mode == 'ResolverSettings':
        urlresolver.display_settings()
