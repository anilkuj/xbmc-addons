'''
    MyStreamsTV plugin for XBMC
    Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

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
import os
import sys
import urllib
import time
import operator


class MyStreamsSchedules:
    def __init__(self):
        self.settings = sys.modules["__main__"].settings
        self.language = sys.modules["__main__"].language
        self.cache = sys.modules["__main__"].cache
        self.common = sys.modules["__main__"].common
        self.xbmc = sys.modules["__main__"].xbmc
        self.xbmcplugin = sys.modules["__main__"].xbmcplugin
        self.xbmcgui = sys.modules["__main__"].xbmcgui
        self.xbmcvfs = sys.modules["__main__"].xbmcvfs

        self.ical_url = "http://cdn.mystreams.me/calendars/%s.list"  # ch01 -> ch30 for channels
        self.schedules = {"30503": "ice_hockey",
                          "30504": "basketball",
                          "30505": "baseball",
                          "30506": "boxing",
                          "30507": "cricket",
                          "30508": "golf",
                          "30509": "motor_sports",
                          "30510": "olympics",
                          "30511": "other_sports",
                          "30512": "rugby",
                          "30513": "soccer",
                          "30514": "tennis",
                          "30515": "tv_shows",
                          "30516": "wrestling_mma",
                          "30517": "american_football"}

        return None

    def fetchSchedule(self, params={}):
        self.common.log(repr(params))

        result = self.common.fetchPage({"link": self.ical_url % params["schedule"]})

        try:
            result = eval(result["content"])
        except:
            self.common.log("Couldn't eval : " + repr(result["content"]) + " - couldn't eval")
            result = []

        for i in range(0, len(result)):
            if "dtstart" in result[i]:
                result[i]["local_start"] = self.convertTimeZone(result[i]["dtstart"])
            if "dtend" in result[i]:
                result[i]["local_end"] = self.convertTimeZone(result[i]["dtend"])
            if "dtstart;value=date" in result[i]:
                result[i]["local_start;value=date"] = self.convertTimeZone(result[i]["dtstart;value=date"])
            if "dtend;value=date" in result[i]:
                result[i]["local_end;value=date"] = self.convertTimeZone(result[i]["dtend;value=date"])

        self.common.log("Done")
        return result

    def getNow(self):
        now = time.time()
        if time.daylight != 0 and False:
            now -= time.altzone - time.timezone
        return now - (3600 * 24 * 0)

    def autoTimeZone(self, value):
        self.common.log(value, 50)  # str_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(value))

        value -= time.timezone
        if time.daylight != 0:
            value += time.daylight * 3600

        self.common.log("Done: " + repr(value), 50)  # str_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(value))
        return value

    def settingsTimeZone(self, value):
        self.common.log(value, 50)
        gmt_offset = int(self.settings.getSetting("gmt_offset"))
        if gmt_offset == 0:
            return 0

        gmt_offset_half = self.settings.getSetting("gmt_offset_half") == "true"
        daylight_saving_time = self.settings.getSetting("daylight_saving_time") == "true"

        if gmt_offset == 1:
            self.common.log("Timezone gmt0", 50)
        elif gmt_offset < 14:
            self.common.log("Timezone gmt+", 50)
            value += 3600 * (gmt_offset - 1)
        elif gmt_offset > 13:
            self.common.log("Timezone gmt-", 50)
            value -= 3600 * (gmt_offset - 1)

        if daylight_saving_time:
            self.common.log("Daylight saving time", 50)
            value += 3600

        if gmt_offset_half:
            self.common.log("gmt + 30 min", 50)
            value += 1800
        return value


    def convertiCalTime(self, org_value):
        try:
            value = time.strptime(org_value, "%Y%m%dT%H%M%SZ")
            value = time.mktime(value)
        except:
            try:
                value = time.strptime(org_value, "%Y%m%dT%H%M%S")  # 20120101T120000
                value = time.mktime(value)
            except:
                try:
                    value = time.strptime(org_value, "%Y%m%d")  # 20120101
                    value = time.mktime(value)
                except:
                    value = 0.0

        return value

    def convertTimeZone(self, value):
        self.common.log(repr(value), 5)
        gmt_offset = int(self.settings.getSetting("gmt_offset"))
        value = self.convertiCalTime(value)
        if value != 0.0:
            if gmt_offset == 0:
                value = self.autoTimeZone(value)
            else:
                value = self.settingsTimeZone(value)
        self.common.log("Done", 5)
        return value

    def getChan(self, chan):
        self.common.log(chan, 5)
        chan = chan.strip()
        org_chan = chan

        items = []
        # First see if only chan number is given
        try:
            items.append({"chan": str(int(chan)), "quality": "", "language": "", "other": ""})
            chan = ""
        except:
            pass

        # Then see if multiple real format channels are given.
        while chan.find("-") == 2 and len(chan) > 0:  # Check if there is a - in the second positon, this matches new new layout.
            if chan.find(";") > -1:
                temp_chan = chan[:chan.find(";")]
                temp_chan = temp_chan.strip()
                chan = chan[chan.find(";") + 1:]
                chan = chan.strip()
            else:
                temp_chan = chan
                chan = ""

            key = ""
            qual = ""
            lang = ""

            if temp_chan.find("-") > 0:
                key = temp_chan[:temp_chan.find("-")]
                temp_chan = temp_chan[temp_chan.find("-") + 1:]

            if temp_chan.find("-") > 0:
                qual = temp_chan[:temp_chan.find("-")]
                temp_chan = temp_chan[temp_chan.find("-") + 1:]

            if len(temp_chan) > 0:
                lang = temp_chan

            items.append({"chan": key, "quality": qual, "language": lang})

        # Finally we try the old version
        if len(items) == 0:
            chan = org_chan.replace("Where", "Chan")
            while chan.find(";") > -1 or chan.find("Chan") > -1:
                if chan.find(";") > -1:
                    temp_chan = chan[:chan.find(";")]
                    temp_chan = temp_chan.strip()
                    chan = chan[chan.find(";") + 1:]
                    chan = chan.strip()
                else:
                    temp_chan = chan
                    chan = ""

                res = self.getChan_old(temp_chan)
                items.append(res)

        self.common.log("Done: " + chan, 5)
        return items

    def getChan_old(self, chan):
        self.common.log(chan, 5)
        if chan.find("-") > -1:
            chan = chan[0:chan.find("-")]

        qual = ""
        lang = ""
        other = ""
        nchan = ""

        while chan.find(" ") > -1 or len(chan) > 0:
            if chan.find(" ") > -1:
                temp = chan[:chan.find(" ")]
                temp = temp.strip()
                chan = chan[chan.find(" ") + 1:]
                chan = chan.strip()
            else:
                temp = chan
                chan = ""

            try:
                nchan = str(int(temp))
            except:
                low = temp.lower()
                if low.find("hd") > -1:
                    qual = temp
                elif low.find("lq") > -1:
                    qual = temp
                elif low.find("spa") > -1:
                    lang = temp
                elif low.find("eng") > -1 or low.find("uk") > -1:
                    lang = temp
                elif low.find("ger") > -1 or low.find("de") > -1:
                    lang = temp
                else:
                    other = temp

        if len(nchan) == 1:
            nchan = "0" + nchan

        res = {"chan": nchan, "quality": qual, "language": lang, "other": other}
        self.common.log("Done: " + repr(res), 5)
        return res

    # Refactor for rPI. This is called with 1771 items, which is too much for the rPI to handle.
    # Maybe it is playingnow that has to be refactored.
    # http://paste.ubuntu.com/1175375/
    def sortSchedule(self, now, items=[], minus_limit=0, plus_limit=0, get_names=False):
        self.common.log("", 5)

        if plus_limit == 0 and minus_limit == 0:
            self.common.log("A +- limiter in seconds must be set")
            return []

        keys_today = {}
        keys = {}
        for i in range(0, len(items)):
            #start = self.convertTimeZone(items[i]["dtstart"])
            #end = self.convertTimeZone(items[i]["dtend"])
            start = items[i]["local_start"]
            end = items[i]["local_end"]
            if start == 0.0:
                self.common.log("Couldn't find any limiter for item : " + repr(items[i]))
            elif (start > now - minus_limit and start < now + plus_limit) or (get_names and start < now and end > now):
                self.common.log("Found match within limits", 0)
                gmstart = time.localtime(start)
                gmnow = time.localtime(now)
                if gmstart.tm_yday == gmnow.tm_yday:
                    keys_today[i] = start
                else:
                    keys[i] = start

        keys = sorted(keys.iteritems(), key=operator.itemgetter(1), reverse=False)
        keys_today = sorted(keys_today.iteritems(), key=operator.itemgetter(1), reverse=False)

        keys = keys_today + keys
        self.common.log("Done", 5)
        self.common.log(repr(keys), 5)
        return keys

    def playingToday(self):
        self.common.log("")
        items = []
        for ical in self.schedules:
            setting = self.settings.getSetting("show_" + ical)
            if not setting or setting == "true":
                items += self.cache.cacheFunction(self.fetchSchedule, {"schedule": self.schedules[ical]})

        now = self.getNow()
        keys_today = self.sortSchedule(now, items, 3600 * 24, 3600 * 24)
        keys = {}
        for i in range(0, len(keys_today)):
            j = keys_today[i][0]
            if "dtstart" in items[j]:
                #start = self.convertTimeZone(items[j]["dtstart"])
                start = items[j]["local_start"]
                if "dtend" in items[j]:
                    #end = self.convertTimeZone(items[j]["dtend"])
                    end = items[j]["local_end"]
                else:
                    end = 0.0

                gmstart = time.localtime(start)
                gmend = time.localtime(end)
                gmnow = time.localtime(now)

                if start == 0.0 or gmstart.tm_yday == gmnow.tm_yday or (gmend.tm_yday == gmnow.tm_yday and (gmend.tm_hour > 0 or gmend.tm_min > 0)):
                    keys[j] = start

        keys = sorted(keys.iteritems(), key=operator.itemgetter(1), reverse=False)
        self.common.log("Done")
        return (items, keys)

    def playingSchedule(self, ical, now):
        self.common.log("")

        items = self.cache.cacheFunction(self.fetchSchedule, {"schedule": self.schedules[ical]})
        if self.settings.getSetting("schedule_plus_limiter") != "":
            schedule_plus_limiter = 3600 * 24 * int(self.settings.getSetting("schedule_plus_limiter"))
        else:
            schedule_plus_limiter = 3600 * 24 * 7

        if self.settings.getSetting("schedule_minus_limiter") != "":
            schedule_minus_limiter = 3600 * 24 * int(self.settings.getSetting("schedule_minus_limiter"))
        else:
            schedule_minus_limiter = 3600 * 24 * 7

        keys = self.sortSchedule(now, items, schedule_minus_limiter, schedule_plus_limiter)

        self.common.log("Done: " + repr(keys))
        return (items, keys)

    def getChannels(self):
        self.common.log("")
        items = []
        for ical in self.schedules:
            items += self.cache.cacheFunction(self.fetchSchedule, {"schedule": self.schedules[ical]})
            self.common.log(self.schedules[ical])

        self.common.log("Done")
        self.common.log(repr(items), 5)
        return items

    def playingNow(self, items):
        self.common.log("")

        now = self.getNow()
        keys_today = self.sortSchedule(now, items, 3600 * 24, 3600 * 24)
        keys = {}

        for i in range(0, len(keys_today)):
            j = keys_today[i][0]
            if "dtstart" in items[j] and "dtend" in items[j] and "summary" in items[j]:
                #start = self.convertTimeZone(items[j]["dtstart"])
                #end = self.convertTimeZone(items[j]["dtend"])
                start = items[j]["local_start"]
                end = items[j]["local_end"]
                if start != 0.0 and start < now and end > now:
                    hstart = time.strftime("%H:%M", time.localtime(start))
                    location = self.getChan(items[j]["location"])

                    for iloc in location:
                        if iloc["chan"] not in keys:
                            keys[iloc["chan"]] = "[%s] %s" % (hstart, items[j]["summary"])
        self.common.log("Done: " + repr(keys))
        return keys

    def playingNext(self, items):
        self.common.log("")

        now = self.getNow()
        keys_today = self.sortSchedule(now, items, 0, 3600 * 24)
        keys = {}

        for i in range(0, len(keys_today)):
            j = keys_today[i][0]
            if "dtstart" in items[j] and "summary" in items[j]:
                #start = self.convertTimeZone(items[j]["dtstart"])
                start = items[j]["local_start"]
                if start != 0.0 and start > now:
                    location = self.getChan(items[j]["location"])
                    hstart = time.strftime("%H:%M", time.localtime(start))

                    for iloc in location:
                        if iloc["chan"] not in keys:
                            keys[iloc["chan"]] = "[%s] %s" % (hstart, items[j]["summary"])

        self.common.log("Done: " + repr(keys))
        return keys

    def channelName(self, items):
        self.common.log("")

        now = self.getNow()

        keys = {}
        for i in range(0, len(items)):
            if "dtstart;value=date" in items[i] and "summary" in items[i] and "dtend;value=date" in items[i]:
                #start = self.convertTimeZone(items[i]["dtstart;value=date"])
                #end = self.convertTimeZone(items[i]["dtend;value=date"])
                start = items[i]["local_start;value=date"]
                end = items[i]["local_end;value=date"]
                if start < now and end > now:
                    location = self.getChan(items[i]["location"])
                    self.common.log(repr(location))

                    for iloc in location:
                        if iloc["chan"] not in keys:
                            keys[iloc["chan"]] = "%s" % (items[i]["summary"])

        self.common.log("Done:  " + repr(keys))
        return keys

    def _getScheduleNameAndUrl(self, now, start, temp_chan, temp_item):
        chan = temp_chan["chan"]
        if temp_chan["language"] != "":
            chan += "-" + temp_chan["language"]

        if temp_chan["quality"] != "":
            chan += "-" + temp_chan["quality"]

        if temp_chan["language"] == "" and temp_chan["quality"] == "" and temp_chan["other"] != "" and False:
            chan += "-" + temp_chan["quality"]

        url = sys.argv[0] + "?path=/root/channels/&action=play_channel&chan=%s" % chan

        if start == 0.0:
            self.common.log("Start1: %s - Org: %s" % (start, now), 5)
            delta = "24/7"
            name = "[%s] %s (#%s)" % (delta, temp_item["summary"], chan)
        else:
            self.common.log("Start2: %s - Org: %s" % (start, now), 5)
            if time.localtime(now).tm_yday == time.localtime(start).tm_yday:
                delta = time.strftime("%H:%M", time.localtime(start))
                if "dtend" in temp_item:
                    #delta += "-" + time.strftime("%H:%M", time.localtime(self.convertTimeZone(temp_item["dtend"])))
                    delta += "-" + time.strftime("%H:%M", time.localtime(temp_item["local_end"]))
            else:
                delta = time.strftime("%d.%b %H:%M", time.localtime(start))
            name = "[%s] %s (#%s)" % (delta, temp_item["summary"], chan)

        return (name, url)

    def getSchedule(self, params={}):
        self.common.log(repr(params))
        if "schedule" in params:
            keys = []
            items = []
            ical = urllib.unquote_plus(params["schedule"])
            now = self.getNow()

            if ical == "30501":
                (items, keys) = self.playingToday()
            else:
                (items, keys) = self.playingSchedule(ical, now)

            inserted = []
            for (i, start) in keys:
                temp_item = items[i]

                channels = self.getChan(temp_item["location"])

                for temp_chan in channels:
                    (name, url) = self._getScheduleNameAndUrl(now, start, temp_chan, temp_item)

                    if name not in inserted:
                        inserted.append(name)
                        listitem = self.xbmcgui.ListItem(name)
                        listitem.setProperty("Video", "true")
                        listitem.setProperty("IsPlayable", "true")
                        plot = temp_item["location"] + " | " + temp_item["summary"] + "\r\n"

                        if start > 0.0:
                            plot += time.strftime("%Y-%m-%d %H:%M", time.localtime(start))
                            if "dtend" in temp_item:
                                #plot += " - " + time.strftime("%Y-%m-%d %H:%M", time.localtime(self.convertTimeZone(temp_item["dtend"])))
                                plot += " - " + time.strftime("%Y-%m-%d %H:%M", time.localtime(temp_item["local_end"]))
                            plot += "\r\n"

                        listitem.setInfo(type='Video', infoLabels={"Title": name, "plot": plot, "Date": start})
                        cm = []
                        cm.append((self.language(30108), "XBMC.Action(Info)",))
                        listitem.addContextMenuItems(cm)

                        self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False, totalItems=len(keys))

            self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_UNSORTED)
            self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_LABEL)
            self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_DATE)
            self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=False)

    def makeListOfSchedules(self, params={}):
        self.common.log("")

        setting = self.settings.getSetting("show_30501")
        name = self.language(30501)
        if not setting or setting == "true":
            self.common.log("Name: %s - Link: %s" % (name, ""), 5)
            url = sys.argv[0] + "?path=/root/schedule/%s&schedule=%s" % (urllib.quote(name), "30501")
            listitem = self.xbmcgui.ListItem(name)
            listitem.setProperty("Folder", "true")

            self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=len(self.schedules) + 1)

        for key in self.schedules.keys():
            name = self.language(int(key))
            self.common.log("Name: %s - Link: %s" % (name, self.schedules[key]), 5)
            setting = self.settings.getSetting("show_" + key)
            if not setting or setting == "true":
                url = sys.argv[0] + "?path=/root/schedule/%s&schedule=%s" % (urllib.quote(name), urllib.quote(key))
                listitem = self.xbmcgui.ListItem(name)
                listitem.setProperty("Folder", "true")

                self.xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=len(self.schedules) + 1)

        self.xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=self.xbmcplugin.SORT_METHOD_LABEL)
        self.xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True, cacheToDisc=False)
