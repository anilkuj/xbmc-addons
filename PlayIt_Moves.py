'''
Created on Dec 27, 2011

@author: ajju
'''
from common.DataObjects import ListItem
from moves import SnapVideo
import xbmcgui #@UnresolvedImport
import xbmc
from common import XBMCInterfaceUtils
import urlresolver

def ping(request_obj, response_obj):
    print request_obj.get_data()
    response_obj.addServiceResponseParam("message", "Hi there, I am PlayIt")

    item = ListItem()
    item.set_next_action_name('pong')
    response_obj.addListItem(item)
    

def playHostedVideo(request_obj, response_obj):
    if XBMCInterfaceUtils.isPlayingVideo():
        response_obj.addServiceResponseParam("status", "error")
        response_obj.addServiceResponseParam("message", "XBMC is already playing a video. Please stop it and try again.")
        item = ListItem()
        item.set_next_action_name('respond')
        response_obj.addListItem(item)
    else:
        video_url = request_obj.get_data()['videoLink']
        video_hosting_info = SnapVideo.findVideoHostingInfo(video_url)
        if video_hosting_info is None:
            streamUrl = urlresolver.HostedMediaFile(video_url).resolve()
            print '***************  calling UrlResolver ******************'
            print streamUrl
            if streamUrl:
                xbmc.Player().play(streamUrl)
                response_obj.addServiceResponseParam("status", "success")
                response_obj.addServiceResponseParam("message", "Enjoy the video!")
                response_obj.set_redirect_action_name('play_it')
                request_obj.get_data()['videoTitle'] = 'PlayIt Video'
            else:
                response_obj.addServiceResponseParam("status", "error")
                response_obj.addServiceResponseParam("message", "Video URL is currently not supported by PlayIt")
                item = ListItem()
                item.set_next_action_name('respond')
                response_obj.addListItem(item)
        else:
            response_obj.addServiceResponseParam("status", "success")
            response_obj.addServiceResponseParam("message", "Enjoy the video!")
            response_obj.set_redirect_action_name('play_it')
            request_obj.get_data()['videoTitle'] = 'PlayIt Video'
        
    
def playRawVideo(request_obj, response_obj):
    video_url = request_obj.get_data()['videoLink']
    
    item = ListItem()
    item.get_moving_data()['videoStreamUrl'] = video_url
    item.set_next_action_name('Play')
    xbmcListItem = xbmcgui.ListItem(label='Streaming Video')
    item.set_xbmc_list_item_obj(xbmcListItem)
    response_obj.addListItem(item)
    response_obj.addServiceResponseParam("status", "success")
    response_obj.addServiceResponseParam("message", "Enjoy the video!")
