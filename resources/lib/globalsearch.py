#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Search Module: Gets user input and updates media list

from urllib import quote_plus, unquote_plus
import xbmc
import xbmcgui
print quote_plus(unicode("*", "UTF-8"))

class Search:
    def __init__(self, text):
        self.text = text

    def search(self):
        listitem = xbmcgui.ListItem(label="Battleship", iconImage='DefaultVideo.png')
        return "Trailers", [listitem]
