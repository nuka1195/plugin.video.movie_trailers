#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Player Module: Plays the selected movie's trailer(s)

from database import Database
from functions import format_date
from urllib import quote_plus
import os
import xbmc
import xbmcgui
import xbmcvfs

WINDOW_DIALOG_EXT_PROGRESS = 10151


class Player(object):
    """Player Class: Plays the passed trailers.

    """

    def play_trailers(self, trailers):
        # create our playlist
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        # clear the playlist if not currently playing video
        if (not xbmc.Player().isPlayingVideo()):
            playlist.clear()
        # iterate thru and add trailer to our playlist
        for trailer in trailers:
            # only add if no errors occurred
            if (trailer[1][6]):
                # set title, we include trailer title also
                title = "{title} - [{trailer}]".format(
                    title=self.m_movie["title"],
                    trailer=trailer[1][1]
                )
                # set our listitem
                listitem = xbmcgui.ListItem(
                    title,
                    iconImage="DefaultVideo.png",
                    thumbnailImage=self.m_movie["thumbnail"]
                )
                # set movie information
                listitem.setInfo(
                    "video", {
                        "title": title,
                        "genre": self.m_movie["genre"],
                        "studio": self.m_movie["studio"],
                        "director": self.m_movie["director"],
                        "Wwriter": self.m_movie["writer"],
                        "mpaa": self.m_movie["mpaa"],
                        "plot": self.m_movie["plot"],
                        "plotoutline": self.m_movie["plot"],
                        "tagLine": "In Theaters {releasedate}".format(
                            releasedate=self.m_movie["releasedate"]
                        )
                    }
                )
                # add user-agent for web URLS
                if (trailer[1][6].startswith("http://")):
                    trailer[1][6] = "{url}|User-Agent={ua}".format(
                        url=trailer[1][6],
                        ua=quote_plus(trailer[1][13])
                    )
                # add item to our playlist
                playlist.add(trailer[1][6], listitem)
                # update DB for watched
                self.m_database.mark_trailer_watched(trailer=trailer[1])

        # play playlist if not currently playing video
        if (not xbmc.Player().isPlayingVideo()):
            xbmc.Player().play(playlist)


class Queue(Player):
    """Queue Class: Queues the selected movie's trailer(s)

    """

    def __init__(self, *args, **kwargs):
        # set our passed addon object
        self.m_addon = kwargs["addon"]
        # set database object
        self.m_database = Database(addon=self.m_addon)

    def queue_trailers(self):
        # get trailer(s) path, local or web
        self._get_trailers()
        # update download queue if needed
        self._update_queue()
        # close database
        self.m_database.close()

    def _update_queue(self):
        # sort out trailers needing to be downloaded,
        trailers_download = []
        trailers_play = []
        # loop thru and set playable and downloadable trailers
        for trailer in self.m_movie["trailers"]:
            # if http:// url and user preference is download, add to download queue
            if (trailer[1][6].startswith("http://") and
                self.m_addon.getSetting("trailer.play.mode") > 0):
                    trailers_download += [trailer]
            else:
                trailers_play += [trailer]
        # play playable trailers
        self.play_trailers(trailers_play)
        # no need to continue if no trailers need downloading
        if (not trailers_download): return
        # set trailers to download for queue
        self.m_movie["trailers"] = trailers_download
        # update queue
        self.m_queue = self.m_database.queue(
            addon_id=self.m_addon.getAddonInfo("id"),
            item=self.m_movie
        )
        # set our total items property
        xbmcgui.Window(WINDOW_DIALOG_EXT_PROGRESS).setProperty(
            key="{id}.items".format(id=self.m_addon.getAddonInfo("id")),
            value=str(len(self.m_queue))
        )
        # start download if not currently downloading
        if (xbmc.getCondVisibility("Window.IsActive({dialog})".format(
                dialog=WINDOW_DIALOG_EXT_PROGRESS)) and
            xbmc.getInfoLabel("Window({dialog}).Property({property})".format(
                dialog=WINDOW_DIALOG_EXT_PROGRESS,
                property=self.m_addon.getAddonInfo("id"))) != ""):
            return
        else:
            from downloader import Download
            Download(
                addon=self.m_addon,
                database=self.m_database,
                queue=self.m_queue,
                play_function=self.play_trailers
            ).download_trailers()

    def _get_trailers(self):
        # check if this is an all HD list
        hd = (
            xbmc.getInfoLabel("Container.Property(PluginCategory)") ==
            self.m_addon.getLocalizedString(30118)
        )
        # check if this is a downloaded list
        downloaded = (
            xbmc.getInfoLabel("Container.Property(PluginCategory)") in [
                self.m_addon.getLocalizedString(30121),
                self.m_addon.getLocalizedString(30122)
            ]
        )
        # fetch trailers
        records = self.m_database.get_trailers(
            idMovie=self.m_addon.params["play"],
            hd=hd,
            downloaded=downloaded
        )
        # set movie info
        self._set_movie_details(records[0])
        # our quality index
        quality = ["Standard", "480p", "720p", "1080p"]
        # we use a dict to eliminate duplicates
        urls = {}
        # iterate thru and find best trailer URL
        for record in records:
            # if better quality or non existent add trailer,
            # formatted with post date for later sorting
            if (not urls.has_key(record[1]) or
                (quality.index(record[2]) > quality.index(urls[record[1]][1][2]))):
                    urls.update({record[1]: [record[4], list(record[:14])]})
        # we only need the values
        self.m_movie["trailers"] = urls.values()
        # sort so trailers are in order of post date
        self.m_movie["trailers"].sort()
        # if multiple trailers
        if (len(self.m_movie["trailers"]) > 1):
            # set choice to play all
            choice = len(self.m_movie["trailers"]) + 1
            # ask
            if (self.m_addon.getSetting("trailer.multiple") == 0):
                # set trailer titles and color
                choices = [
                    "[COLOR {color}]{downloaded}{trailer}   {min:0d}:{sec:02d}   {posted}   ({quality})[/COLOR]".format(
                        color=["unwatched", "watched"][trailer[1][7] > 0],
                        downloaded=["", "* "][trailer[1][10] is not None],
                        trailer=trailer[1][1],
                        min=divmod(trailer[1][3], 60)[0],
                        sec=divmod(trailer[1][3], 60)[1],
                        quality=trailer[1][2],
                        posted=format_date(
                            date=trailer[1][4],
                            pretty=False,
                            short=True
                        )
                    )
                    for trailer in self.m_movie["trailers"]
                ]
                # add random and play all choices
                choices += [
                    "[ {option} ]".format(option=self.m_addon.getLocalizedString(30232)),
                    "[ {option} ]".format(option=self.m_addon.getLocalizedString(30233))
                ]
                # get user choice
                choice = xbmcgui.Dialog().select(self.m_movie["title"], choices)
            # random trailer
            if (self.m_addon.getSetting("trailer.multiple") == 1 or
                choice == len(self.m_movie["trailers"])):
                    import random
                    # iterate thru and eliminate watched trailers
                    tlrs = [tlr for tlr in self.m_movie["trailers"] if tlr[1][7] < 1]
                    # if there are unwatched trailers set them, otherwise use all
                    if (tlrs):
                        self.m_movie["trailers"] = tlrs
                    # get random trailer
                    choice = random.randint(0, len(self.m_movie["trailers"]) - 1)
            # choose trailer
            if (choice == -1):
                self.m_movie["trailers"] = []
            elif (choice < len(self.m_movie["trailers"])):
                self.m_movie["trailers"] = [self.m_movie["trailers"][choice]]
        # iterate thru and check if trailer exists
        for count, trailer in enumerate(self.m_movie["trailers"]):
            # if file was downloaded use it
            self.m_movie["trailers"][count][1][6] = trailer[1][10] or trailer[1][6]
            # set download path if not already downloaded
            self.m_movie["trailers"][count][1][10] = (
                trailer[1][10] or
                self._get_legal_filepath(
                    self.m_movie["title"],
                    trailer[1][6]
                )
            )

    def _set_movie_details(self, record):
        # set movie details
        self.m_movie = {
            "idMovie": record[17],
            "title": record[18],
            "mpaa": record[19],
            "studio": record[20],
            "releasedate": record[21],
            "year": int(record[21][:4] or 0),
            "copyright": record[22],
            "director": record[23],
            "writer": record[24],
            "plot": record[25],
            "cast": record[26],
            "genre": record[27],
            "poster": record[28],
            "thumbnail": "{url}|User-Agent={ua}".format(
                url=record[28],
                ua=quote_plus(record[13])
            )
        }

    def _get_legal_filepath(self, title, url, id_=0):
        # set our default filename and extension
        file_, ext = os.path.splitext(os.path.basename(url))
        # does user want to use title as filename
        file_ = [file_, title][self.m_addon.getSetting("trailer.use.title")]
        # set identifier
        trailer_id = ""
        if (id_ > 0):
            trailer_id = " ({id})".format(id="ABCDEFGHIJKLMNOPQRSTUVWXYZ"[id_])
        # set our default trailer text
        trailer = ["", "-trailer"][self.m_addon.getSetting("trailer.add.trailer")]
        # set our default file path (if play_mode is temp, download to cache folder)
        if (self.m_addon.getSetting("trailer.play.mode") == 1):
            filepath = "special://temp/"
        else:
            filepath = self.m_addon.getSetting("trailer.save.folder") or "special://temp/"
        # do we want to save with movie
        if (self.m_addon.getSetting("trailer.save.movie")):
            filepath, file_, trailer = self._get_movie_path(
                title,
                filepath,
                file_,
                trailer
            )
        # set final filename
        file_ = "{name}{id}{trailer}{ext}".format(
            name=os.path.splitext(file_)[0],
            id=trailer_id,
            trailer=trailer,
            ext=ext
        )
        # FIXME: may need changing for temorary download
        # if file already exists add an ID and try again
        if (filepath != "special://temp/" and
                xbmcvfs.exists(xbmc.makeLegalFilename(xbmc.validatePath(
                    os.path.join(
                        xbmc.translatePath(filepath),
                        file_
                    )
                )).decode("UTF-8"))):
            return self._get_legal_filepath(title, url, id_ + 1)

        # return final path
        return xbmc.makeLegalFilename(xbmc.validatePath(
                os.path.join(
                    xbmc.translatePath(filepath),
                    file_
                )
            )).decode("UTF-8")

    def _get_movie_path(self, title, filepath, file_, trailer):
        # check if movie exists
        moviepath = self.m_database.get_xbmc_library_path(title)
        # if movie found set path
        if (moviepath is not None):
            # set filepath and file, we ignore movies extension later on
            filepath, file_ = os.path.split(moviepath)
            # always add -trailer when saving to a movies folder
            trailer = "-trailer"

        return filepath, file_, trailer
