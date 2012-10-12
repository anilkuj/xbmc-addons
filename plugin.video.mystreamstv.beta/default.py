import sys
import time
import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs
import socket
import xbmcaddon
import cookielib
import urllib2

socket.setdefaulttimeout(30.0)  # 10s seems to be too little for soccer

settings = xbmcaddon.Addon(id='plugin.video.mystreamstv.beta')
language = settings.getLocalizedString

cookiejar = cookielib.LWPCookieJar()
cookie_handler = urllib2.HTTPCookieProcessor(cookiejar)
opener = urllib2.build_opener(cookie_handler)

# plugin constants
version = "0.8.0"
plugin = "SmoothStreams.tv Beta-" + version
author = "SmoothStreams"
url = "www.xbmc.com"
dbg = settings.getSetting("dbg") == "true"
dbglevel = 3
core = ""
scheduler = ""
cache = ""
common = ""
downloader = ""

if (__name__ == "__main__" ):
    print plugin + " ARGV: " + repr(sys.argv)

    try:
        import StorageServer
        cache = StorageServer.StorageServer("mystream", 2)
    except:
        import storageserverdummy as StorageServer
        cache = StorageServer.StorageServer("mystream", 2)

    try:
        import CommonFunctions
        common = CommonFunctions
        common.plugin = plugin
    except:
        common = False

    try:
        import SimpleDownloader as downloader
        downloader = downloader.SimpleDownloader()
    except:
        downloader = False

    import MyStreamsSchedules
    scheduler = MyStreamsSchedules.MyStreamsSchedules()

    import MyStreamsCore
    core = MyStreamsCore.MyStreamsCore()

    if (not settings.getSetting("firstrun")):
        settings.openSettings()
        settings.setSetting("firstrun", "1")

    if not sys.argv[2]:
        core.makeMain()
        if settings.getSetting("username") != "" and settings.getSetting("user_password") != "":
            core.login()

        if settings.getSetting("auto_server") == "true":
            if xbmc.getCondVisibility("system.platform.windows") or xbmc.getCondVisibility("system.platform.linux") or xbmc.getCondVisibility("system.platform.osx") or xbmc.getCondVisibility("system.platform.android"):
                core.testServers(True)

        if (not settings.getSetting("install_count") or float(settings.getSetting("install_count")) < time.time()):
            core.countInstall()
            settings.setSetting("install_count", str(time.time() + (60*24*14)))
    else:
        core.navigation(sys.argv[2])
