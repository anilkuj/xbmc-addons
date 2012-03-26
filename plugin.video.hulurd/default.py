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


DB = os.path.join(xbmc.translatePath("special://database"), 'hulu.db')
BASE_URL = 'http://www.hulu.com'
AZ_DIRECTORIES = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y', 'Z']
GENRES = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 
          'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy', 
          'History', 'Horror', 'Music', 'Musical', 
          'Mystery', 'Romance', 'Sci-Fi', 'Short', 'Sport', 
          'Thriller', 'War', 'Western']
net = Net()
addon = Addon('plugin.video.hulurd', sys.argv)
mysettings = xbmcaddon.Addon(id='plugin.video.hulurd')
DATA_PATH = os.path.join(xbmc.translatePath('special://profile/addon_data/plugin.video.hulurd'), '')
cookie_jar = os.path.join(DATA_PATH, "cookiejar.lwp")

##### Queries ##########
mode = addon.queries['mode']
url = addon.queries.get('url', None)
section = addon.queries.get('section', None)
img = addon.queries.get('img', None)
title = addon.queries.get('title', None)
genre = addon.queries.get('genre', None)
letter = addon.queries.get('letter', None)
page = addon.queries.get('page', None)
episodes = addon.queries.get('episodes', None)


def unicode_urlencode(value): 
	if isinstance(value, unicode): 
		return urllib.quote(value.encode("utf-8"))
	else: 
		return urllib.quote(value)

def initDatabase():
	print "Building hulu Database"
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
        print 'hulu get Movie Titles Menu %s' % url
        html = net.http_GET(url).content
        #match = re.compile('title="Watch online: (.+?)".+?href="(.+?)".+?src="(.+?)".+?span title="(.+?)"', re.MULTILINE | re.DOTALL | re.IGNORECASE).findall(html)
        match = re.compile('title="Watch online: (.+?)".+?href="(.+?)".+?src="(.+?)"').findall(html)
        for name, url, img in match:
                #name = name + '  ( ' +  rating + ' )'
                if section == 'tv' and episode == False:
                        addon.add_directory({'mode': 'GetSeasons', 'section': section, 'url': BASE_URL + url, 'img': BASE_URL + img }, {'title':  name}, img=BASE_URL + img)
                else: 
                        addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': BASE_URL + url}, {'title':  name}, img=BASE_URL + img)
       	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetHuluVideo(section, url, title, img): # Get Hulu Video
        print 'In GetHuluVideo %s' %url
        dialog = xbmcgui.Dialog()
        if mysettings.getSetting('realdebrid-account') == 'false':
                dialog.ok(' Real-Debrid ', ' Please enter your real-debrid credentials in addon settings', '', '')
                return
        
        if login(cookie_jar):
                print 'Logged in Sucessfully'
        else:
                dialog.ok(' Real-Debrid ', ' Please check your real-debrid credentials ', '', '')
                return
        try:
                url = 'http://real-debrid.com/ajax/deb.php?lang=en&sl=1&link=%s' % url
                if cookie_jar is not None and os.path.exists(cookie_jar):
                        rdNet = Net(cookie_file=cookie_jar)
                        source = rdNet.http_GET(url).content
                else:
                        dialog.ok(' Real-Debrid ', ' Cookie file missing, Try again. ', '', '')
        except Exception, e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            dialog.ok(' Real-Debrid ', ' Real-Debrid server timed out ', '', '')
            return None
        print '************* %s' % source
        
        if re.search('Upgrade your account now to generate a link', source):
            dialog.ok(' Real-Debrid ', ' Upgrade your account now to generate a link ', '', '')
            return None
        if source == '<span id="generation-error">Your file is unavailable on the hoster.</span>':
            dialog.ok(' Real-Debrid ', ' Your file is unavailable on the hoster ', '', '')
            return None
        if re.search('This hoster is not included in our free offer', source):
            dialog.ok(' Real-Debrid ', ' This hoster is not included in our free offer ', '', '')            
            return None
        if re.search('No server is available for this hoster.', source):
            dialog.ok(' Real-Debrid ', ' No server is available for this hoster ', '', '')            
            return None
        link =re.compile('ok"><a href="(.+?)"').findall(source)

        if len(link) > 0:
                for video in link:
                        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                        playlist.clear()
                        listitem = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
                        #if section == 'tv': listitem.setInfo('video', {'TVShowTitle': title, 'Season': season, 'Episode': episode } )		
                        playlist.add(url=video, listitem=listitem)
        xbmc.Player().play(playlist)


def  checkLogin(cookie_jar):
        url = 'http://real-debrid.com/lib/api/account.php'
        if not os.path.exists(cookie_jar):
               return True
        source =  net.http_GET(url).content
        if re.search('expiration', source):
            return False
        else:
            return True
    
def login(cookie_jar):
        if checkLogin(cookie_jar): 
            login_data = urllib.urlencode({'user' : mysettings.getSetting('realdebrid-username'), 'pass' : mysettings.getSetting('realdebrid-password')})
            url = 'https://real-debrid.com/ajax/login.php?' + login_data
            source = net.http_GET(url).content
            if re.search('OK', source):
                net.save_cookies(cookie_jar)
                net.set_cookies(cookie_jar)
                return True
            else:
                return False
        else:
            return True


def GetDomain(url):
        tmp = re.compile('//(.+?)/').findall(url)
        domain = 'Unknown'
        if len(tmp) > 0 :
            domain = tmp[0].replace('www.', '')
        return domain

def MainMenu():  #homescreen
        #addon.add_directory({'mode': 'LoadCategories', 'section': 'movies'}, {'title':  'Movies'})
	addon.add_directory({'mode': 'LoadCategories', 'section': 'tv'}, {'title':  'TV Shows'})
        addon.add_directory({'mode': 'ResolverSettings'}, {'title':  'Resolver Settings'})
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        
def LoadCategories(section): #Categories
         
        #addon.add_directory({'mode': 'BrowseAtoZ', 'section': section}, {'title':  'A-Z'})
	#addon.add_directory({'mode': 'BrowseGenre', 'section': section}, {'title':  'Genres'})
	addon.add_directory({'mode': 'BrowseLatest', 'section': section}, {'title':  'Latest'})
	#addon.add_directory({'mode': 'GetTitles', 'section': section}, {'title':  'Favorites'})
	addon.add_directory({'mode': 'Search', 'section': section}, {'title':  'Search'})
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

def BrowseLatest(section=None):
        print 'Browse Latest screen'
        url = BASE_URL + '/released/episodes'
        html = net.http_GET(url).content
	episodes = re.compile('hover"><a href="(.+?)".+?<img src="(.+?)".+?alt="(.+?) \(', re.DOTALL).findall(html)
	for url, img, title in episodes:
                print url
                print title
                print img
                addon.add_directory({'mode': 'GetHuluVideo', 'section': section, 'url': url, 'title': title, 'img': img}, {'title':  title}, img= img)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def GetSearchQuery(section):
	last_search = ADDON.load_data('search')
	if not last_search: last_search = ''
	keyboard = xbmc.Keyboard()
	if section == 'tv': keyboard.setHeading('Search TV Shows')
	else: keyboard.setHeading('Search Movies')
	keyboard.setDefault(last_search)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		search_text = keyboard.getText()
		addon.save_data('search',search_text)
		Search(section, keyboard.getText())
	else:
                return

def GetResults(section=None, genre=None, letter=None, page=None): 
	print 'Filtered results for Section: %s Genre: %s Letter: %s Page: %s' % \
			(section, genre, letter, page)
	if section == 'tv':	xbmcplugin.setContent( int( sys.argv[1] ), 'tvshows' )
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
                        addon.add_directory({'mode': 'GetEpisodes', 'section': section, 'img': img, 'episodes': episodes}, {'title':  season_name}, img= img)
		xbmcplugin.endOfDirectory(int(sys.argv[1]))


def GetEpisodes(section, img, episodes): 
	xbmcplugin.setContent( int( sys.argv[1] ), 'episodes' )
	r = 'href=(.+?)">(.+?)<'
	episodes = re.compile(r, re.DOTALL).findall(episodes) 
	for epurl, title in episodes:
		print '%s @ %s' %(title, epurl)
                addon.add_directory({'mode': 'GetLinks', 'section': section, 'url': BASE_URL + epurl}, {'title':  title}, img=BASE_URL + img)
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
elif mode == 'GetResults': 
	GetResults(section, genre, letter, page)
elif mode == 'GetTitles': 
	GetTitles(url)
elif mode == 'GetHuluVideo':
	GetHuluVideo(section, url, title, img)
elif mode == 'GetSeasons':
	GetSeasons(section, url, img)
elif mode == 'GetEpisodes':
	GetEpisodes(section, img, episodes)
elif mode == 'Search':
	GetSearchQuery(section)
elif mode == 'ResolverSettings':
        urlresolver.display_settings()
