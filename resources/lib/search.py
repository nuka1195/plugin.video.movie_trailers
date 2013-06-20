#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Search Module: Gets user input and updates media list

from urllib import quote_plus
import xbmc
import xbmcgui


class Search:
    """Search Class: Gets users search criteria and updates media list."""

    def __init__(self, *args, **kwargs):
        # set our passed addon object
        self.m_addon = kwargs["addon"]

    def search(self):
        # get search string
        search = unicode(
            xbmcgui.Dialog().input(
                heading=self.m_addon.getLocalizedString(30731),
                default=self.m_addon.getSetting("search.text")
            ),
            "UTF-8"
        )
        # skip if user cancels dialog or enters empty search
        if (not search): return

        # save text for next search
        self.m_addon.setSetting("search.text", search)

        # if user preference is to limit search to current listing
        # we need to set category and append previous searches
        category = ""
        if (self.m_addon.getSetting("search.current.list")):
            category = self.m_addon.params.get("category", u"")
            if (self.m_addon.params.get("search", u"")):
                search = self.m_addon.params.get("search", u"") + u" - " + search

        # update our list with new search
        xbmc.executebuiltin(
            u"Container.Update(plugin://{path}?category={category}&search={search})".format(
                path=self.m_addon.getAddonInfo("Id"),
                category=quote_plus(repr(category)),
                search=quote_plus(repr(search))
            )
        )
