#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Helper Module: Shared functions between trailer scrapers

from functions import format_date
import os
import socket
import urllib2
import xbmc
import xbmcvfs
import xbmcgui


class Helper:
    """Shared functions between trailer scrapers

    """

    def __init__(self, *args, **kwargs):
        # set our passed info
        self.m_addon = kwargs["addon"]
        self.encoding = kwargs.get("encoding", "UTF-8")
        self.headers = kwargs.get("headers", {})
        # add user-agent and If-Modified-Since header
        self.headers.update({
            "User-Agent": kwargs["useragent"],
            "If-Modified-Since": format_date(kwargs["sourcedate"], modified=True)
        })

    def backup_source(self, source_date):
        # nothing to backup if no source date
        if (source_date is None): return
        # set paths
        old_path = xbmc.validatePath(
            os.path.join(
                xbmc.translatePath(self.m_addon.getSetting("source.cache.path")),
                self.m_addon.getSetting("trailer.scraper"),
                u"source"
            )
        ).decode("UTF-8")
        new_path = xbmc.validatePath(
            os.path.join(
                xbmc.translatePath(self.m_addon.getSetting("source.cache.path")),
                self.m_addon.getSetting("trailer.scraper"),
                u"source-{date}".format(date=source_date.split(" ")[0])
            )
        ).decode("UTF-8")
        # if folder exists, copy it
        if (xbmcvfs.exists(old_path) and not xbmcvfs.exists(new_path)):
            xbmcvfs.rename(old_path, new_path)

    def get_source(self, url, skip304=False):
        # we use a cachename as basename's may be identical
        cachename = u"{name}.xml".format(
            name=os.path.splitext(xbmc.getCacheThumbName(url))[0]
        )
        # set path and URL
        base_path = xbmc.validatePath(
            os.path.join(
                xbmc.translatePath(self.m_addon.getSetting("source.cache.path")),
                self.m_addon.getSetting("trailer.scraper"),
                u"source",
                cachename[0],
                cachename
            )
        ).decode("UTF-8")
        #############################################
        #return self._get_source_from_file(base_path)
        #############################################
        try:
            # FIXME: change this to urlretrieve and use a report hook?
            # TODO: maybe support Accept-Encoding": "gzip, deflate", "Content-Type" added in scrapers headers
            # request URL
            request = urllib2.Request(url, headers=self.headers)
            # read source
            source = self._unescape_text(
                unicode(urllib2.urlopen(request).read(), self.encoding)
            )
        except (socket.timeout, urllib2.URLError, urllib2.HTTPError) as error:
            # reset source
            source = None
            # if not a "not modified" error (304) log message
            if (error.errno != 304):
                xbmc.log(
                    "Helper::get_source - {error} - {url}".format(
                        error=str(error),
                        url=url
                    ),
                    level=xbmc.LOGERROR
                )
            # TODO: do we want this (IIRC it's for AMT Full)
            # get source from file
            if (not skip304 and error.errno == 304):
                source = self._get_source_from_file(base_path)
        else:
            # TODO: do something with ok, or, do not return true/false from _save_source()
            # save the source for future parsing
            ok = self._save_source(source, base_path)

        return source

    @staticmethod
    def _unescape_text(text):
        # replace escaped entities and return result
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&apos;", "'").replace("&quot;", "\"")
        text = text.replace("&amp;", "&").replace("&#151;", u"\u2014")
        text = text.replace("&amp ", "& ").replace("&#038;", "&")
        text = text.replace("&#039;", "'").replace("&#169;", u"\u00A9")

        return text

    def download_trailers(self, limit=0):
        # TODO: finish this download function, only do when updating in the background?
        # FIXME: maybe have a setting instead of limit, also maybe make it MB not trailer number
        pass

    @staticmethod
    def _get_source_from_file(base_path):
        try:
            # load source from file
            source = unicode(xbmcvfs.File(base_path, "r").read(), "UTF-8")
            # if no source raise error
            if (not source):
                raise IOError(2, "Unable to open source!", base_path)
        except IOError as error:
            # reset source
            source = None
            # log error
            xbmc.log(
                "Helper::_get_source_from_file - {error} - {path}".format(
                    error=str(error),
                    path=base_path
                ),
                level=xbmc.LOGERROR
            )

        return source

    @staticmethod
    def _save_source(source, base_path):
        try:
            # if the path to the source file does not exist create it
            if (not xbmcvfs.mkdirs(os.path.dirname(base_path))):
                raise IOError(
                    1,
                    "Unable to make dir structure!",
                    os.path.dirname(base_path)
                )
            # save source
            if (not xbmcvfs.File(base_path, "w").write(source.encode("UTF-8"))):
                raise IOError(2, "Unable to save source!", base_path)
        except IOError as error:
            # log error
            xbmc.log(
                "Helper::_save_source - {error} - {path}".format(
                    error=str(error),
                    path=base_path
                ),
                level=xbmc.LOGERROR
            )
            return False
        else:
            # success
            return True

    @staticmethod
    def format_source_date(source_date, hours=0):
        # return properly formatted date
        return format_date(source_date, reverse=True, modified=True, hours=hours)

    def progress_dialog(self, count=0, total=0, message=""):
        if (count == 0):
            self.pDialog = xbmcgui.DialogProgressBG()
            self.pDialog.create(
                heading="{addon}: {message}".format(
                    addon=self.m_addon.getAddonInfo("name"),
                    message=message
                )
            )
        elif (count > 0):
            percent = 0
            if (total >= count):
                percent = int((float(count) / total) * 100)
            self.pDialog.update(
                percent=percent,
                heading="{addon}: {message}".format(
                    addon=self.m_addon.getAddonInfo("name"),
                    message=message
                ),
                message="{count} of {total} - ({percent:d}%)".format(
                    count=count,
                    total=total,
                    percent=percent
                )
            )
        else:
            self.pDialog.close()

    def notification(self, message):
        xbmcgui.Dialog().notification(
            heading=self.m_addon.getAddonInfo("name"),
            message=message,
            icon=self.m_addon.getAddonInfo("icon"),
            time=5000
        )
