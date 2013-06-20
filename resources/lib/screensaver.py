#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Movie Trailers: Video plugin

import xbmc


class Screensaver(object):

    def __init__(self, *args, **kwargs):
        self.start()

    def start(self):
        #xbmc.Player().play("/Users/scottjohns/Trailers/monstersuniversity-tlr1_h640w-trailer.mov")
        # create our playlist
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        playlist.add("/Users/scottjohns/Trailers/monstersuniversity-tlr1_h640w-trailer.mov")
        xbmc.Player().play(playlist)
