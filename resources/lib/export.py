#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Export Module: Exports trailer info to an NFO file as XML

from functions import format_date
import os
import xbmc
import xbmcvfs


class Export(object):
    """Exports trailer info to an NFO file as XML and
       copies thumbnail.

    """

    def __init__(self, *args, **kwargs):
        # set class variables
        self.movie = kwargs.get("movie", None)
        self.trailer = kwargs.get("trailer", None)
        self.filepath = kwargs.get("filepath", None)
        # update dialog not None
        if (kwargs.get("dialog", None) is not None):
            kwargs["dialog"].update(
                heading="{heading}: {action}".format(
                    heading=kwargs["addon"].getAddonInfo("name"),
                    action=kwargs["addon"].getLocalizedString(30830))
            )

    def create_nfo_file(self):
        # set movie info
        nfoSource = self.nfo_file_format().format(
            title=self._escape_text(self.movie["title"]),
            mpaa=self.movie["mpaa"],
            studio=self._escape_text(self.movie["studio"]),
            releasedate=format_date(self.movie["releasedate"], reverse=True),
            copyright=self.movie["copyright"],
            director=self._escape_text(self.movie["director"]),
            writer=self._escape_text(self.movie["writer"]),
            plot=self._escape_text(self.movie["plot"]),
            cast=self._escape_text(self.movie["cast"]),
            genre=self._escape_text(self.movie["genre"]),
            poster=self.movie["thumbnail"].split("|")[0],
            trailertitle=self._escape_text(self.trailer[1][1]),
            quality=self.trailer[1][2],
            runtime=self.trailer[1][3],
            postdate=self.trailer[1][4],
            size=self.trailer[1][5],
            url=self.trailer[1][6]
        )

        # save NFO source to file
        return self._save_nfo_file(nfoSource)

    def _save_nfo_file(self, nfoSource):
        try:
            # create NFO path
            nfopath = u"{root}.nfo".format(root=os.path.splitext(self.filepath)[0])
            # save NFO file
            if (not xbmcvfs.File(nfopath, "w").write(nfoSource.encode("UTF-8"))):
                raise IOError(2, "Unable to save source!", nfopath)
        except IOError as error:
            # notify user what error occurred
            xbmc.log("Export::_save_nfo_file - {error} - {path}".format(
                error=error.strerror, path=error.filename), level=xbmc.LOGERROR)
            # failure
            return False
        else:
            # save thumb
            self._save_thumb()
            # success
            return True

    def _save_thumb(self):
        # create thumb cache path
        cached_thumb = os.path.join(
            xbmc.translatePath("special://thumbnails/"),
            xbmc.getCacheThumbName(self.movie["thumbnail"])[0],
            xbmc.getCacheThumbName(self.movie["thumbnail"]).replace(
                ".tbn", os.path.splitext(self.movie["thumbnail"].split("|")[0])[1])
        ).decode("UTF-8")
        # create saved thumb path
        saved_thumb = u"{root}.tbn".format(
            root=os.path.splitext(self.filepath)[0]  #,
            #ext=os.path.splitext(self.movie["thumbnail"].split("|")[0])[1]
        ).decode("UTF-8")
        # copy thumb
        xbmcvfs.copy(cached_thumb, saved_thumb)

    @staticmethod
    def _escape_text(text):
        # escape special XML entities
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")\
                   .replace("\"", "&quot;").replace("'", "&apos;")

    @staticmethod
    def nfo_file_format():
        # set NFO file format
        return u"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movieinfo>
    <title>{title}</title>
    <mpaa>{mpaa}</mpaa>
    <studio>{studio}</studio>
    <releasedate>{releasedate}</releasedate>
    <copyright>{copyright}</copyright>
    <director>{director}</director>
    <writer>{writer}</writer>
    <plot>{plot}</plot>
    <cast>{cast}</cast>
    <genre>{genre}</genre>
    <poster>{poster}</poster>
    <trailer title="{trailertitle}" quality="{quality}" runtime="{runtime}" postdate="{postdate}" size="{size}">{url}</trailer>
</movieinfo>
"""
