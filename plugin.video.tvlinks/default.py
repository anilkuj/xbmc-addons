import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urllib2
import re, string, sys, os
import urlresolver
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
import datetime as dt
import HTMLParser
from metahandler import metahandlers
import sys, traceback


try:
	from sqlite3 import dbapi2 as sqlite
	print "Loading sqlite3 as DB engine"
except:
	from pysqlite2 import dbapi2 as sqlite
	print "Loading pysqlite2 as DB engine"

prepare_zip = False
metaget=metahandlers.MetaData(preparezip=prepare_zip)

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

enableMeta = True

if plugin.getSetting('enableMeta') == 'false':
        enableMeta = False

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
season = addon.queries.get('season', None)
imdbnum = addon.queries.get('imdbnum', None)

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
        match = re.compile('<li> <a href="(.+?)".+?c1">(.+?)<.+?c2">(.*?)<').findall(html)
        for url, name, year in match:
                if section == 'tv':
                        if enableMeta:
                                print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ %s' % name
                                meta = metaget.get_meta('tvshow', name, year)
				if meta['imdb_id'] =='' and meta['tvdb_id'] =='':
					meta = metaget.get_meta('tvshow', name)

				addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url},
                                                    meta, img= meta['cover_url'], fanart= meta['backdrop_url'], total_items=len(match))
                        else:
                                addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url}, {'title':  name}, total_items=len(match))
                else: 
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': BASE_URL + url,
                                             'startPage': '1', 'numOfPages': pages}, {'title':  name}, img=BASE_URL + img, total_items=len(match))
        setView('tvshows', 'tvshows-view')
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
                                addon.add_directory({'mode': 'PlayVideo', 'section': section, 'url': gatewayId, 'listitem': listitem}, {'title':  name}, total_items=len(match))
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
        return lastPage
        

def PlayVideo(section, gatewayId, listitem):
        url = 'http://www.tv-links.eu/gateway.php?data='+gatewayId
        res = net.http_GET(url)
        finalurl = res.get_url()
        stream_url = urlresolver.HostedMediaFile(finalurl).resolve()
        xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(stream_url, listitem)


def MainMenu():  #homescreen

	addon.add_directory({'mode': 'BrowseLatest', 'section': 'tv'}, {'title':  'Latest'})
	addon.add_directory({'mode': 'BrowsePopular', 'section': 'tv'}, {'title':  'Popular'})
        addon.add_directory({'mode': 'BrowseAtoZ', 'section': 'tv'}, {'title':  'A-Z'})
	addon.add_directory({'mode': 'BrowseGenre', 'section': 'tv'}, {'title':  'Genres'})
	if Login():
                addon.add_directory({'mode': 'Favorites', 'section': 'tv'}, {'title':  'Favorites'})
	addon.add_directory({'mode': 'GetSearchQuery', 'section': 'tv'}, {'title':  'Search'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        
def BrowseAtoZ(section=None, genre=None): 
	print 'Browse by alphabet screen'
	addon.add_directory({'mode': 'GetResults', 'section': section, 'genre': genre, 'letter': '0-9'}, {'title':  '#'})
	for character in AZ_DIRECTORIES:
                addon.add_directory({'mode': 'GetResults', 'section': section, 'genre': genre, 'letter': character}, {'title':  character})
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def BrowseLatest(section=None):
        print 'Browse Latest screen'
        xbmcplugin.setContent( int( sys.argv[1] ), 'tvshows' )
        d = dt.datetime.now() - dt.timedelta( days = 1 )
        latest = '%d/%d/%d' %(d.month, d.day, d.year)
        url = BASE_URL + '/schedule.html?date=' + latest
        html = net.http_GET(url).content
        match = re.compile('width="45" alt="(.+?)".+?c2 brd_r_dot"><a href="(.+?)">Season (.+?), Episode (.+?)<.+?em><a.+?>(.+?)<', re.MULTILINE | re.DOTALL).findall(html)
        imdbnum = None
        for title, url, seasonNum, episodeNum, episodeTitle in match:
                name = title + ' S' +  seasonNum + 'xE' + episodeNum + ' : ' + episodeTitle
                titleurl = BASE_URL + url
                url = BASE_URL + url + 'video-results/'
                imdbnum = ''
                temp = titleurl.partition('season_')
                titleurl = temp[0]
                ephtml = net.http_GET(titleurl).content
                r = re.search('imdb.com/title/(.+?)/', ephtml, re.DOTALL)
                if r: imdbnum = r.group(1)
                if enableMeta and imdbnum:
                        try:
				meta = metaget.get_episode_meta(name=episodeTitle,imdb_id=imdbnum,season=seasonNum, episode=episodeNum)
			except Exception as e:
				meta['cover_url'] = ''
				meta['backdrop_url'] = ''
				print 'Error %s for %s season %s episode %s with imdbnum %s' % (e, title,seasonNum,episodeNum,imdbnum)
                                #print "*** print_exc:"
                                #traceback.print_exc()
			meta['title'] = name
			addon.add_directory({'mode': 'GetLinks', 'url': url, 'startPage':'1', 'numOfPages': pages},
                                                    meta, img= meta['cover_url'], fanart= meta['backdrop_url'], total_items=len(match))
                else:
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': url, 'startPage': '1', 'numOfPages': pages}, {'title':  name}, total_items=len(match))
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
                

def BrowsePopular(section=None):
        print 'Browse Popular screen'
        xbmcplugin.setContent( int( sys.argv[1] ), 'tvshows' )
        url = BASE_URL
        html = net.http_GET(url).content
        match = re.compile('<li> <a href="(.+?)".+?bigger">(.+?)<').findall(html)
        if section == 'tv':
                for url, name in match:
                        if enableMeta:
                                meta = metaget.get_meta('tvshow', name, '0')
				if meta['imdb_id'] =='' and meta['tvdb_id'] =='':
					meta = metaget.get_meta('tvshow', name)

				addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url},
                                                    meta, img= meta['cover_url'], fanart= meta['backdrop_url'], total_items=len(match))
                        else:
                                addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url}, {'title':  name}, total_items=len(match))
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
        print 'In search'
        setView('tvshows', 'tvshows-view')
        url = BASE_URL + '/_search/?s='  + query
        html = net.http_GET(url).content
        print 'got search results'
        match = re.findall('<li> <a href="(.+?)".+?bold">(.+?)<.+?Released:<.+?(\d\d\d\d)', html)
        print len(match)
        for url, name, year in match:
                if  'tv-shows' in url:
                        if enableMeta:
                                name = name.encode('utf-8')
                                print name
                                meta = metaget.get_meta('tvshow', name, year)
				if meta['imdb_id'] =='' and meta['tvdb_id'] =='':
					meta = metaget.get_meta('tvshow', name)
				if meta['cover_url'] in ('/images/noposter.jpg',''):
                                        meta['cover_url'] = img
				addon.add_directory({'mode': 'GetSeasons', 'section': 'tv', 'url': BASE_URL + url},
                                                    meta, img= meta['cover_url'], fanart= meta['backdrop_url'], total_items=len(match))
                        else:
                                addon.add_directory({'mode': 'GetSeasons', 'section': 'tv', 'url': BASE_URL + url}, {'title':  name}, total_items=len(match))
        print 'end of for loop'
	setView('tvshows', 'tvshows-view')
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
        seasons = re.findall('onclick="seasonShow\(\'([\d]+)\'', html)
        r = re.search('<h1.+?/">(.+?)<.+?imdb.com/title/(.+?)/', html, re.DOTALL)
        title = ''
        imdbnum = ''
        if r: title, imdbnum = r.groups()
        season_meta = []
        if enableMeta:
                        try :
                                season_meta = metaget.get_seasons(title, imdbnum, seasons)
                        except Exception as e:
                                print 'Error retrieveing  season meta %s' % e
                                print "*** print_exc:"
                                traceback.print_exc()
        shows = re.compile("Season (\d+)<\/div>(.+?)<.a> <.li> <.ul>", re.DOTALL).findall(html)
        num = 0
	if shows:
		for season_name, episodes in shows:
                        if enableMeta and imdbnum:
                                try: meta = season_meta[num]
                                except: meta = {'cover_url': '',  'backdrop_url': ''}
                                season_name = 'Season ' + season_name
                                meta['title'] = season_name
                                if not meta['cover_url']: meta['cover_url'] = meta['backdrop_url']
                                addon.add_directory({'mode': 'GetEpisodes', 'section': section, 'episodes': episodes.encode("utf-8"), 'season': meta['season'], 'imdbnum': imdbnum},
                                                    meta, img= meta['cover_url'], fanart= meta['backdrop_url'], total_items=len(shows))
                        else:
                                season_name = 'Season ' + season_name
                                addon.add_directory({'mode': 'GetEpisodes', 'section': section, 'episodes': episodes.encode("utf-8")}, {'title':  season_name}, total_items=len(shows))
                        num += 1

	shows = re.compile("Season (\d+) <em(.+?)<.a> <.li> <.ul>", re.DOTALL).findall(html)   
	if shows:
		for season_name, episodes in shows:
                        if enableMeta and imdbnum:
                                try: meta = season_meta[num]
                                except: meta = {'cover_url': '',  'backdrop_url': ''}
                                season_name = 'Season ' + season_name
                                meta['title'] = season_name
                                if not meta['cover_url']: meta['cover_url'] = meta['backdrop_url']
                                addon.add_directory({'mode': 'GetEpisodes', 'section': section, 'episodes': episodes.encode("utf-8"), 'season': meta['season'], 'imdbnum': imdbnum},
                                                    meta, img= meta['cover_url'], fanart= meta['backdrop_url'], total_items=len(shows))
                        else:
                                season_name = 'Season ' + season_name
                                addon.add_directory({'mode': 'GetEpisodes', 'section': section, 'episodes': episodes.encode("utf-8")}, {'title':  season_name}, total_items=len(shows))
                        num += 1
        setView('seasons', 'seasons-view')
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetEpisodes(section, episodes, season= None, imdbnum= None): 
	xbmcplugin.setContent( int( sys.argv[1] ), 'episodes' )
	r = 'href="(.+?)".+?c1">(.+?)<.+?c2">(.+?)<'
	episodes = re.compile(r, re.DOTALL).findall(episodes)
	
	for epurl, epnum, eptitle in episodes:
		title = epnum + ' : ' + eptitle
		url = BASE_URL + epurl + 'video-results/'
		meta = {}
		if enableMeta and imdbnum:
                        try:
                                epnum = epnum.partition(' ')
				meta = metaget.get_episode_meta(name=eptitle,imdb_id=imdbnum,season=int(season), episode=int(epnum[2]))
			except Exception as e:
				meta['cover_url'] = ''
				meta['backdrop_url'] = ''
                                print "*** print_exc:"
                                traceback.print_exc()
			meta['title'] = title.decode("utf-8")
			print 'adding dir'
			addon.add_directory({'mode': 'GetLinks', 'url': url, 'startPage':'1', 'numOfPages': pages},
                                                   meta, img= "", fanart= "", total_items=len(episodes))
                else:
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': url, 'startPage':'1', 'numOfPages': pages}, {'title':  title.decode("utf-8")}, total_items=len(episodes))
	setView('episodes', 'episodes-view')
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
                                if '/tv-shows/' in url:
                                        if enableMeta:
                                                year = '0'
                                                r = re.search('-(\d\d\d\d)\.', img)
                                                if r: year = r.group(1)
                                                meta = metaget.get_meta('tvshow', title, year)
                                                if meta['imdb_id'] =='' and meta['tvdb_id'] =='':
                                                        meta = metaget.get_meta('tvshow', title)
                                                addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url},
                                                                    meta, img= meta['cover_url'], fanart= meta['backdrop_url'], total_items=len(match))
                                        else:
                                                addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url}, {'title':  name}, total_items=len(match))
		setView('tvshows', 'tvshows-view')
                xbmcplugin.endOfDirectory(int(sys.argv[1]))

def setView(content, viewType):
	# set content type so library shows more views and info
	if content:
		xbmcplugin.setContent(int(sys.argv[1]), content)
	if addon.get_setting('auto-view') == 'true':
		xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.get_setting(viewType) )

	# set sort methods - probably we don't need all of them
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )


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
	GetEpisodes(section, episodes, season, imdbnum)
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
