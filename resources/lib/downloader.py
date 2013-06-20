#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Player Module: Plays the selected movie's trailer(s)

from export import Export
import os
import socket
import time
import urllib
import urllib2
import xbmc
import xbmcgui
import xbmcvfs

WINDOW_DIALOG_EXT_PROGRESS = 10151


class ProgressDialog(object):

    def __init__(self, *args, **kwargs):
        # set Addon class
        self.m_addon = kwargs["addon"]
        # create background progress dialog
        self.pDialog = xbmcgui.DialogProgressBG()
        self.pDialog.create(self.m_addon.getAddonInfo("name"))

    def set_heading(self, heading):
        self.heading = heading

    def set_time(self):
        self.start_time = self.current_time = time.time()

    def update(self, percent=0, heading=" ", message=" "):
        self.pDialog.update(percent, heading, message)

    def close(self):
        self.pDialog.close()

    def report_hook(self, block_count, block_size, total_size):
        def _format_bytes(B, size=True):
            # calculate KB/MB
            KB = B / 1024
            MB = KB / 1024
            # set correct formatter, amount and specifier
            formatter = [
                "{amount:1.0f}{specifier}",
                "{amount:1.0f}{specifier}",
                "{amount:3.1f}{specifier}"
            ][(KB >= 1) + (MB >= 1)]
            amount = [B, KB, MB][(KB >= 1) + (MB >= 1)]
            specifier = self.m_addon.getLocalizedString(
                (30722 - (7 * size)) + (KB >= 1) + (MB >= 1)
            )

            # return formatted bytes
            return formatter.format(amount=amount, specifier=specifier)

        def _calc_speed():
            # return formatted speed
            return _format_bytes(bytes_complete / elapsed_time, size=False)

        def _calc_eta():
            # return formatted ETA
            return "{0:1.0f}:{1:02.0f}".format(
                *divmod(
                    long(float(total_size - bytes_complete) /
                    (bytes_complete / elapsed_time)), 60
                )
            )

        def _limit_rate(now, elapsed_time, bytes_complete):
            # limit rate?, 1550 is no limit
            if (self.m_addon.getSetting("download.rate.limit") ==
                self.m_addon.constants["DOWNLOAD_RATE_NO_LIMIT"]):
                    return
            # set sleep time
            sleep_time = int(((
                    bytes_complete /
                    1024 /
                    self.m_addon.getSetting("download.rate.limit")
                ) - (now - self.start_time)) * 1000
            )
            # sleep to adjust download rate
            if (sleep_time > 0):
                xbmc.sleep(sleep_time)

        # TODO: raise a keyboardInterrupt error if user cancelled download
        if (xbmc.abortRequested): raise KeyboardInterrupt  # self.pDialog.isFinished()
        # no progress if background?
        # we use a background progress dialog, so maybe a setting to hide
        # background updates?
        #if (self.background):
        #   return
        # get current time
        now = time.time()
        # only update enough to make display stable
        if ((now - self.current_time) < 0.2 or block_count == 0): return
        # set new amounts
        self.current_time = now
        elapsed_time = now - self.start_time
        bytes_complete = float(block_count * block_size)
        percent_complete = int(bytes_complete * 100 / total_size)
        # set message
        message = "{complete} {of} {size} {at} {speed} {eta} {time} {min} - ({percent:d}%)".format(
            complete=_format_bytes(bytes_complete),
            of=self.m_addon.getLocalizedString(30718),
            size=_format_bytes(float(total_size)),
            at=self.m_addon.getLocalizedString(30719),
            speed=_calc_speed(),
            eta=self.m_addon.getLocalizedString(30720),
            time=_calc_eta(),
            min=self.m_addon.getLocalizedString(30721),
            percent=percent_complete
        )
        # update dialog
        self.update(
            percent=percent_complete,
            heading=self.heading.format(
                items=xbmc.getInfoLabel("Window({dialog}).Property({property}.items)".format(
                    dialog=WINDOW_DIALOG_EXT_PROGRESS,
                    property=self.m_addon.getAddonInfo("id")))
            ),
            message=message
        )
        # limit rate?, 1550 is no limit
        _limit_rate(now, elapsed_time, bytes_complete)


class Download(object):
    """Download Class: Downloads trailers for playback

    """

    def __init__(self, *args, **kwargs):
        # set addon object
        self.m_addon = kwargs["addon"]
        # set database object
        self.m_database = kwargs["database"]
        # set database object
        self.m_queue = kwargs["queue"]
        # set playback function
        self.play_trailers = kwargs["play_function"]

    def download_trailers(self):
        try:
            self.pDialog = ProgressDialog(addon=self.m_addon)
            # set our isalive property
            xbmcgui.Window(WINDOW_DIALOG_EXT_PROGRESS).setProperty(
                key=self.m_addon.getAddonInfo("id"),
                value="True"
            )
            # loop while queue isn't empty
            while self.m_queue and not xbmc.abortRequested:
                # break out of loop if no queue
                self.m_movie = self.m_queue[0]
                # iterate thru and download trailers
                for self.count, trailer in enumerate(self.m_movie["trailers"]):
                    # override user-agent,
                    # we do it here as different scrapers have different user-agents
                    class _urlopener(urllib.FancyURLopener):
                        version = trailer[1][13]
                    urllib._urlopener = _urlopener()
                    # set filepath
                    self.filepath = trailer[1][10]
                    # format title for progress heading
                    title = "{basename}{trailer}".format(
                        basename=os.path.basename(self.filepath),
                        trailer=[
                            "",
                            " ({count:d} {of} {total:d})".format(
                                count=self.count + 1,
                                of=self.m_addon.getLocalizedString(30718),
                                total=len(self.m_movie["trailers"]))
                        ][len(self.m_movie["trailers"]) > 1]
                    )
                    # set progress dialog heading
                    self.pDialog.set_heading(
                        "{heading}: [{{items}}] {action} {title}".format(
                        heading=self.m_addon.getAddonInfo("name"),
                        action=self.m_addon.getLocalizedString(30710 +
                            (self.m_addon.getSetting("trailer.play.mode") == 2)),
                        title=title),
                        )
                    # set current time
                    self.pDialog.set_time()
                    # check if temporary download exists
                    if (not xbmcvfs.exists(self.filepath)):
                        # fetch the video
                        info = urllib.urlretrieve(
                            trailer[1][6],
                            self.filepath,
                            self.pDialog.report_hook
                        )
                        # set new size, necessary for AMT Lite's 1080p trailers
                        # as we use 720p source for trailer info
                        self.m_movie["trailers"][self.count][1][5] = info[1].getheader(
                            "Content-Length",
                            self.m_movie["trailers"][self.count][1][5]
                        )
                        # create NFO and copy thumb
                        self._finalize_download()
                    # set URL to filepath
                    self.m_movie["trailers"][self.count][1][6] = self.filepath
                    # play trailers
                    self.play_trailers([self.m_movie["trailers"][self.count]])

                # update queue
                self.m_queue = self.m_database.queue(
                    addon_id=self.m_addon.getAddonInfo("id"),
                    item=0
                )
                # set our total items property
                xbmcgui.Window(WINDOW_DIALOG_EXT_PROGRESS).setProperty(
                    key="{id}.items".format(id=self.m_addon.getAddonInfo("id")),
                    value=str(len(self.m_queue))
                )
                # clear isalive property if no queue
                if (not self.m_queue):
                    xbmcgui.Window(WINDOW_DIALOG_EXT_PROGRESS).setProperty(
                        key=self.m_addon.getAddonInfo("id"),
                        value=""
                    )

        except (KeyboardInterrupt, urllib2.URLError, socket.timeout, IOError) as error:
            # oops, notify user what error occurred if not KeyboardInterrupt
            if (error.args):  # is not None):
                xbmc.log("Download::download_trailers - {error} - {url}".format(
                        error=str(error),
                        url=trailer[1][6]
                    ),
                    level=xbmc.LOGERROR
                )
            # clear URL so trailer doesn't stream
            self.m_movie["trailers"][self.count][1][6] = ""
            # clean cache
            urllib.urlcleanup()
            # filepath is not always released immediately,
            # we may need to try more than one attempt, sleeping between
            remove_tries = 3
            # try 3 times to cleanup
            while remove_tries and xbmcvfs.exists(self.filepath):
                if (xbmcvfs.delete(self.filepath)):
                    break
                remove_tries -= 1
                xbmc.sleep(1000)
        # close dialog
        if (self.pDialog is not None):
            self.pDialog.close()

    def _finalize_download(self):
        # do not update database for temp downloads
        if (self.filepath.startswith(xbmc.translatePath("special://temp/"))):
            return
        # TODO: Do something with ok
        # create NFO file and copy thumb
        ok = Export(
                addon=self.m_addon,
                movie=self.m_movie,
                trailer=self.m_movie["trailers"][self.count],
                filepath=self.filepath,
                dialog=self.pDialog
            ).create_nfo_file()
        # update trailer
        self.m_database.mark_trailer_downloaded(
            trailer=self.m_movie["trailers"][self.count][1]
        )
