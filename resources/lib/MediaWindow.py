#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## MediaWindow Module: Helper functions for populating media lists

import os
import xbmcgui
import xbmcplugin


class _ButtonIndexError:
    pass


class DirectoryItem:
    """
        DirectoryItem: Helper functions for formatting listitems
    """
    def __init__(self):
        # clear attributes
        self.url = None
        self.listitem = None
        self.context = []
        self.isFolder = False
        self.totalItems = 0

    def addContextMenuItem(self, label, action):
        # add menu item to our list
        self.context += [(label, action,)]


class MediaWindow:
    """
        MediaWindow Class: Helper functions for populating media lists
    """
    # constants
    BUTTON_MAX = 5

    def __init__(self, hId, addon, wId=None, content=None, links=[]):
        # initialize xbmcaddon module
        self.m_addon = addon
        # set our handle id
        self.m_handle = hId
        # set our window buttons
        self.m_links = links
        # reset button counter
        self.m_buttonId = 0
        # get the current window if no window id supplied
        if (wId is None):
            self.m_window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        else:
            self.m_window = xbmcgui.Window(wId)
        # set plugin category
        self._set_plugin_category(self.m_addon.getSetting("plugin.category"))
        # set plugin content
        self._set_media_content(content)
        # set plugin sortmethods
        self._set_sort_methods(content == "addoncategories", self.m_addon.getSetting("label2mask"))
        # set fanart
        self._set_fanart(self.m_addon.getAddonInfo("id"), self.m_addon.getSetting("fanart"))

    def addItem(self, item):
        # add context menu items to listitem with replaceItems = True so only ours show
        if (item.context):
            item.listitem.addContextMenuItems(item.context, replaceItems=True)
        # add directory item
        return xbmcplugin.addDirectoryItem(handle=self.m_handle, url=item.url, listitem=item.listitem, isFolder=item.isFolder, totalItems=item.totalItems)

    def addItems(self, items):
        # add directory items
        return xbmcplugin.addDirectoryItems(handle=self.m_handle, items=items, totalItems=len(items))

    def end(self, succeeded=True, cacheToDisc=True):
        # set window quick links
        self._set_quick_links(succeeded and self.m_links)
        # send notification we're finished, successfully or unsuccessfully
        xbmcplugin.endOfDirectory(handle=self.m_handle, succeeded=succeeded, cacheToDisc=cacheToDisc)

    def _set_plugin_category(self, category=None):
        # if plugin set category
        if (category is not None):
            # set plugin category
            xbmcplugin.setPluginCategory(handle=self.m_handle, category=category)

    def _set_media_content(self, content):
        # set media content, if user passed plugin content
        if (content is not None):
            xbmcplugin.setContent(handle=self.m_handle, content=content)

    def _set_sort_methods(self, categories, label2mask):
        # get sort methods
        if (categories):
            sortmethods = [
                xbmcplugin.SORT_METHOD_LABEL
            ]
        else:
            sortmethods = [
                xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE,
                #xbmcplugin.SORT_METHOD_SIZE,
                xbmcplugin.SORT_METHOD_DATE,
                xbmcplugin.SORT_METHOD_MPAA_RATING,
                #xbmcplugin.SORT_METHOD_VIDEO_RUNTIME,
                #xbmcplugin.SORT_METHOD_GENRE,
                #xbmcplugin.SORT_METHOD_STUDIO
            ]
        # enumerate thru and add each sort method
        for sortmethod in sortmethods:
            xbmcplugin.addSortMethod(handle=self.m_handle, sortMethod=sortmethod, label2Mask=label2mask)

    def _set_fanart(self, addonId, fanart):
        # if user passed fanart tuple (image, category path,)
        if (fanart is None):
            # if no user preferred fanart set for skin fanart
            fanart_image = os.path.join(addonId + "{id}-fanart.png".format(id=addonId))
        else:
            if (fanart[1] is not None):
                # set category image
                fanart_image = os.path.join(fanart[1] + "{category}.png".format(category=fanart[2].split(": ")[0]))
            else:
                # set user preference image
                fanart_image = fanart[0]
        # set fanart
        xbmcplugin.setPluginFanart(handle=self.m_handle, image=fanart_image)

    def _set_quick_links(self, ok):
        # only set links on a successful directory listing
        if (ok):
            # set links heading
            self.m_window.setProperty("AddonButtons.Heading", self.m_links[0])
            # enumerate thru and set each link
            for label, onclick, onfocus, onunfocus in self.m_links[1]:
                # set quick link
                self._set_quick_link(label, onclick, onfocus, onunfocus)
            # set search link
            self.m_window.setProperty("AddonSearch.OnClick", self.m_links[2])
            # set settings link
            self.m_window.setProperty("AddonSettings.OnClick", self.m_links[3])
        # clear remaing quick link properties
        self._clear_quick_links()

    def _set_quick_link(self, label, onclick=None, onfocus=None, onunfocus=None):
        # increment m_buttonId
        self.m_buttonId += 1
        # if it's not a valid button id raise button error
        if (self.m_buttonId > self.BUTTON_MAX):
            raise _ButtonIndexError
        # set quick link label property
        self.m_window.setProperty("AddonButton.%d.Label" % self.m_buttonId, label)
        # set optional quick link properties
        if (onclick is not None):
            self.m_window.setProperty("AddonButton.%d.OnClick" % self.m_buttonId, onclick)
        if (onfocus is not None):
            self.m_window.setProperty("AddonButton.%d.OnFocus" % self.m_buttonId, onfocus)
        if (onunfocus is not None):
            self.m_window.setProperty("AddonButton.%d.OnUnFocus" % self.m_buttonId, onunfocus)

    def _clear_quick_links(self):
        # we want to clear all remaining quick links
        for bId in range(self.m_buttonId + 1, self.BUTTON_MAX + 1):
            self.m_window.clearProperty("AddonButton.%d.Label" % bId)
            self.m_window.clearProperty("AddonButton.%d.OnClick" % bId)
            self.m_window.clearProperty("AddonButton.%d.OnFocus" % bId)
            self.m_window.clearProperty("AddonButton.%d.OnUnFocus" % bId)
