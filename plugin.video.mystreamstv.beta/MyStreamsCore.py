'''
    MyStreamsTV plugin for XBMC
    Copyright (C) 2012 SmoothStreams

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import re
import subprocess

class MyStreamsCore:
    def __init__(self):
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.common = sys.modules["__main__"].common
        self.cache = sys.modules["__main__"].cache
        self.downloader = sys.modules["__main__"].downloader
        self.xbmc = sys.modules["__main__"].xbmc
        self.xbmcgui = sys.modules["__main__"].xbmcgui
        self.xbmcplugin = sys.modules["__main__"].xbmcplugin
        self.scheduler = sys.modules["__main__"].scheduler

        self.servers = ["dEU.SmoothStreams.tv", "dNA.SmoothStreams.tv", "dSG.SmoothStreams.tv"]

        return None

    def makeChannelList(self):
        self.common.log("")
        size = 40


        if self.settings.getSetting("show_now_next") == "true":
            items = self.cache.cacheFunction(self.scheduler.getChannels)
            #items = self.scheduler.getChannels()
            channel_name = self.scheduler.channelName(items)
            playing_now = self.scheduler.playingNow(items)
            playing_next = self.scheduler.playingNext(items)
        else:
            channel_name = {}
            playing_now = {}
            playing_next = {}

        for chan in range(1, size + 1):
            if chan < 10:
                chan = "0" + str(chan)
            else:
                chan = str(chan)

            name = "#" + chan

            if chan in channel_name:
                name += " - " + channel_name[chan].decode("utf-8")
                playing = "%s %s - %s\r\n" % (self.language(30101), chan, channel_name[chan].decode("utf-8"))
            else:
                playing = "%s %s\r\n" % (self.language(30101), chan)

            if chan in playing_now:
                playing = "%s: %s\r\n" % (self.language(30106), playing_now[chan].decode("utf-8"))
                name += " - Now: " + playing_now[chan].decode("utf-8")

            if chan in playing_next:
                if chan not in playing_now or playing_next[chan] != playing_now[chan]:
                    try:
                        playing += "%s: %s\r\n" % (self.language(30107), playing_next[chan].decode("utf-8"))
                    except: # Unicode utf8 python crap.
                        pass
                    name += " - Next: " + playing_next[chan].decode("utf-8")

            listitem = self.xbmcgui.ListItem(label=name)
            listitem.setProperty("Video", "true")
            listitem.setProperty("IsPlayable", "true")
            listitem.setInfo(type='Video', infoLabels={"Title": name, "plot": playing})
            cm = []
            if self.downloader:
                cm.append((self.language(30103), "XBMC.RunPlugin(%s?path=%s&action=download&chan=%s)" % (sys.argv[0], "/root/channels/", chan)))
            cm.append((self.language(30108), "XBMC.Action(Info)",))
            listitem.addContextMenuItems(cm)

            url = sys.argv[0] + "?path=/root/channels/&action=play_channel&chan=%s" % chan
            self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False, totalItems=size)

        self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=False)
        self.common.log("Done")

    def getChanUrl(self, params={}):
        self.common.log(repr(params))
        get = params.get

        server = self.servers[int(self.settings.getSetting("server"))]

        if self.settings.getSetting("high_def") == "true":
            quality = "q1"  # HD - 2800k
        elif True:
            quality = "q2"  # LD - 1250k
        else:
            quality = "q3"  # Mobile - 400k ( Not in settings)

        chan = get("chan")
        uname = self.settings.getSetting("SUserN")
        pword = self.settings.getSetting("SPassW")

        if self.settings.getSetting("service") == "1":
            self.common.log("Using Live247.tv")
            stream_port = "2935"
        elif self.settings.getSetting("service") == "3":
            self.common.log("Using StarStreams")
            stream_port = "3935"
        else:
            self.common.log("Using Mystreams/uSport")
            stream_port = "29350"

        if self.settings.getSetting("server_type") == "0":
            stream_type = "rtmp"
            chan_template = "%s://%s:%s/view?u=%s&p=%s/ch%s%s.stream"
            url = chan_template % (stream_type, server, stream_port, uname, pword, chan, quality)
        else:
            stream_type = "rtsp"
            chan_template = "%s://%s:%s/view/ch%s%s.stream?u=%s&p=%s"
            url = chan_template % (stream_type, server, stream_port, chan, quality, uname, pword)


        if self.settings.getSetting("show_now_next") == "true":
            items = self.cache.cacheFunction(self.scheduler.getChannels)
            channel_name = self.scheduler.channelName(items)
            playing_now = self.scheduler.playingNow(items)
            playing_next = self.scheduler.playingNext(items)
        else:
            channel_name = {}
            playing_now = {}
            playing_next = {}

        name = "#" + chan

        if chan in channel_name:
            name += " - " + channel_name[chan].decode("utf-8")

        if chan in playing_now:
            name += " - Now: " + playing_now[chan].decode("utf-8")

        if chan in playing_next:
            if chan not in playing_now or playing_next[chan] != playing_now[chan]:
                name += " - Next: " + playing_next[chan].decode("utf-8")

        self.common.log("Done")
        return (name, url)

    def playChan(self, params={}):
        self.common.log("")
        (name, url) = self.getChanUrl(params)
        listitem = self.xbmcgui.ListItem(name, path=url)
        # listitem.setInfo(type='Video', infoLabels=video)
        self.xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
        self.common.log("Done")

    def download(self, params={}):
        self.common.log("")
        get = params.get
        filename = self.common.getUserInput(self.language(30104))
        minutes = self.common.getUserInputNumbers(self.language(30105))
        if not minutes:
            self.common.log("No duration set")
            return None

        (name, url) = self.getChanUrl(params)

        if len(url) > 10:
            if not self.settings.getSetting("download_path"):
                self.showMessage(self.language(30600), self.language(30601))
                self.settings.openSettings()

            download_path = self.settings.getSetting("download_path")

            if download_path:
                video = {"live": "true",
                         "url": url,
                         "download_path": download_path,
                         "duration": int(minutes) * 60,
                         "Title": filename
                         }

                if filename.find(".") == -1:
                    self.common.log("Adding .avi to filename")
                    filename += ".avi"

                if get("async"):
                    self.downloader.download(filename, video, async=False)
                else:
                    self.downloader.download(filename, video)

        self.common.log("Done")

    def makeMain(self):
        self.common.log("")
        size = 3

        url = sys.argv[0] + "?path=/root/channels"
        listitem = self.xbmcgui.ListItem(self.language(30100))
        listitem.setProperty("Folder", "true")
        self.common.log("Channels url: %s, handle: %s" % (url, sys.argv[1]))
        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=size)

        url = sys.argv[0] + "?path=/root/schedules"
        listitem = self.xbmcgui.ListItem(self.language(30102))
        listitem.setProperty("Folder", "true")
        self.common.log("Schedules url: %s, handle: %s" % (url, sys.argv[1]))
        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=size)

        url = sys.argv[0] + "?path=/root&action=settings"
        listitem = self.xbmcgui.ListItem(self.language(30200))
        listitem.setProperty("Folder", "true")
        self.common.log("Settings url: %s, handle: %s" % (url, sys.argv[1]))
        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=size)

        self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=False)
        self.common.log("Done")

    def setService(self):
        if self.settings.getSetting("service") == "0":
            self.common.log("Using mystreams.tv")
            return {"login": "http://mystreams.tv/go/wp-login.php",
                    "addip": "http://mystreams.tv/go/chansurf.php"}
        elif self.settings.getSetting("service") == "1":
            self.common.log("Using Live247.tv")
            return {"login": "http://live247.tv/vai/wp-login.php",
                    "addip": "http://live247.tv/vai/chansurf.php"}
        elif self.settings.getSetting("service") == "2":
            self.common.log("Using usport.tv")
            return {"login": "http://usport.tv/go/wp-login.php?action=login",
                    "addip": "http://usport.tv/go/chansurf.php"}
        elif self.settings.getSetting("service") == "3":
            self.common.log("Using starstreams.tv")
            return {"login": "http://starstreams.tv/wp-login.php",
                    "addip": "http://starstreams.tv/wp-content/surf/chansurf.php"}
        else:
            self.common.log("Unsupported service found: " + repr(self.settings.getSetting("service")))
            return {}

    def countInstall(self):
        self.common.log("")
        if self.settings.getSetting("service") == "1":
            self.common.log("Using Live247.tv")
            url = "http://smoothstreams.tv/auth/countxbmc247.php"
        elif self.settings.getSetting("service") == "3":
            self.common.log("Using starstreams.tv")
            url = "http://smoothstreams.tv/auth/countxbmcss.php"
        else:
            self.common.log("Using mystreams.tv/usport.tv")
            url = "http://smoothstreams.tv/auth/countxbmcms.php"

        uname = self.settings.getSetting("username")

        result = self.common.fetchPage({"link": url, "post_data": {"user": uname, "date": ""}})
        self.common.log("Done: " + result["content"].strip())

    def login(self):
        self.common.log("")
        urls = self.setService()
        result = self.common.fetchPage({"link": urls["login"]})
        uname = self.settings.getSetting("username")
        pword = self.settings.getSetting("user_password")

        post_data = {"log": uname,
                     "pwd": pword,
                     "user_login": uname,
                     "user_pass": pword,
                     "rememberme": "forever",
                     "wp-submit": "Log in",
                     "testcookie": "1"}

        result = self.common.fetchPage({"link": urls["login"], "post_data": post_data, "refering": urls["login"], "hide_post_data": "true"})

        if result["content"].find("LOG OUT") > -1 or result["content"].find("logout") > -1:
            self.common.log("Login complete")
            self.getStreamLogin(urls)
            return True
        else:
            self.common.log("Login failure: " + repr(result))
            return False

    def averageList(self, lst):
        self.common.log(repr(lst), 5)
        avg_ping = 0
        avg_ping_cnt = 0
        for p in lst:
            try:
                avg_ping += float(p)
                avg_ping_cnt += 1
            except:
                self.common.log("Couldn't convert %s to float" % repr(p))
        self.common.log("Done", 5)
        return avg_ping / avg_ping_cnt

    def testServers(self, update_settings=False):
        self.common.log("")
        self.common.log("Original server: " + self.servers[int(self.settings.getSetting("server"))] + " - " + self.settings.getSetting("server"))
        res = ""
        ping = False
        for i, server in enumerate(self.servers):
            if self.xbmc.getCondVisibility('system.platform.windows'):
                p = subprocess.Popen(["ping", "-n", "4", server], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            else:
                p = subprocess.Popen(["ping", "-c", "4", server], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
            ping_results = re.compile("time=(.*?)ms").findall(p.communicate()[0])
            self.common.log("Server %s - %s: n%s" % (i, server, repr(ping_results)))
            avg_ping = self.averageList(ping_results)
            if avg_ping != 0:
                if avg_ping < ping or not ping:
                    res = server
                    ping = avg_ping
                    if update_settings:
                        self.common.log("Updating settings")
                        self.settings.setSetting("server", str(i))
            else:
                self.common.log("Couldn't get ping")
        self.common.log("Done %s: %s" % (res, ping))
        return res

    def getStreamLogin(self, urls):
        self.common.log("")
        self.settings.setSetting("SUserN", "")
        self.settings.setSetting("SPassW", "")
        if True:
            result = self.common.fetchPage({"link": urls["addip"]})

            scripts = self.common.parseDOM(result["content"], "script")
            self.common.log("Scripts: " + repr(scripts), 3)

            for script in scripts:
                if script.find("var UserN") > -1:
                    login = re.compile("var UserN='(.*?)'; var PassW='(.*?)'").findall(script)
                    self.common.log("Login: " + repr(login), 3)
                    if len(login) == 1:
                        self.settings.setSetting("SUserN", login[0][0])
                        self.settings.setSetting("SPassW", login[0][1])
                        return True
        return False

    def showMessage(self, heading, message):
        #duration = ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10][int(self.settings.getSetting('notification_length'))]) * 1000
        duration = 5
        self.xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % (heading, message, duration))

    def navigation(self, params):
        params = self.common.getParameters(params)
        get = params.get

        self.common.log(repr(params))

        if get("path") == "/root/channels":
            self.makeChannelList()
        elif get("path") == "/root/schedules":
            self.scheduler.makeListOfSchedules()
        elif get("action") == "settings":
            self.settings.openSettings()
            if self.settings.getSetting("username") != "" and self.settings.getSetting("user_password") != "":
                self.login()
        elif get("action") == "login":
            self.login()
        elif get("action") == "play_channel":
            self.playChan(params)
        elif get("action") == "download":
            self.download(params)
        elif get("schedule") != None:
            self.scheduler.getSchedule(params)

        self.common.log("Done")
