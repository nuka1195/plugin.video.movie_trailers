#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## GUI Module for Movie Showtimes

import sys
import xbmc
import xbmcgui
from urllib import unquote_plus
import datetime

XML_WINDOW = "custom_movie.trailers-showtimes.xml"

class GUI(xbmcgui.WindowXMLDialog):
    """
        GUI class: used for viewing movie showtimes.
    """
    # default actions
    ACTION_CLOSE_DIALOG = (9, 10,)

    def __init__(self, *args, **kwargs):
        # init Dialog class
        xbmcgui.WindowXMLDialog.__init__(self)  #, *args, **kwargs)
        # set our Addon class
        self.Addon = kwargs["addon"]
        # parse argv for any params
        self._parse_argv()
        # get user preferences
        self._get_settings()
        # grab all the info for the movie
        self._get_trailer_info()
        # get proper scraper
        self._get_scraper()
        # show dialog
        self.doModal()

    def onInit(self):
        # set initial trailer info
        self._show_trailer_info()
        # search for showtimes for trailer selected
        self._get_showtimes(movie=self.params["showtimes"], day=self.settings["showtimes_scraper_day"])

    def onAction(self, action):
        # only action is close
        if (action in self.ACTION_CLOSE_DIALOG):
            self._close_dialog()

    def onClick(self, controlId):
        self._get_selection(self.getControl(100).getSelectedPosition())

    def onFocus(self, controlId):
        pass

    def _parse_argv(self):
        # parse sys.argv for params; we need to eval() as quote_plus and unicode do not work well together and we used repr()
        self.params = dict([arg.split("=")[0], eval(unquote_plus(arg.split("=")[1]))] for arg in sys.argv[1].split("&") if (arg))

    def _get_trailer_info(self):
        # initialize our dictionary
        self.movie_showtimes = {}
        # set our studio
        self.movie_showtimes["title"] = self.params["showtimes"]
        # set our studio
        self.movie_showtimes["studio"] = unicode(xbmc.getInfoLabel("ListItem.Studio"), "UTF-8")
        # set our studio
        self.movie_showtimes["director"] = unicode(xbmc.getInfoLabel("ListItem.Director"), "UTF-8")
        # set our genre
        self.movie_showtimes["genre"] = unicode(xbmc.getInfoLabel("ListItem.Genre"), "UTF-8")
        # set our rating
        self.movie_showtimes["mpaa"] = unicode(xbmc.getInfoLabel("ListItem.MPAA"), "UTF-8")
        # set our thumbnail
        self.movie_showtimes["poster"] = unicode(xbmc.getInfoImage("ListItem.Thumb"), "UTF-8")
        # set our plotoutline
        self.movie_showtimes["plot"] = unicode(xbmc.getInfoLabel("ListItem.Plot"), "UTF-8")
        # set our released date
        self.movie_showtimes["releasedate"] = xbmc.getInfoLabel("ListItem.Property(releasedate)")
        # set our trailer duration
        self.movie_showtimes["duration"] = xbmc.getInfoLabel("ListItem.Duration")
        # set cast list
        self.movie_showtimes["cast"] = unicode(" / ".join(xbmc.getInfoLabel("ListItem.Cast").split("\n")), "UTF-8")

    def _show_trailer_info(self):
        # create date
        date = datetime.date.today() + datetime.timedelta(days=int(self.settings["showtimes_scraper_day"]))
        self.movie_showtimes["date"] = date.strftime(self.settings["date_format"])
        # set initial apple trailer info
        self._set_title_info(
            title=self.params["showtimes"],
            duration=self.movie_showtimes["duration"],
            mpaa=self.movie_showtimes["mpaa"],
            genre=self.movie_showtimes["genre"],
            #studio=self.movie_showtimes["studio"],
            director=self.movie_showtimes["director"],
            cast=self.movie_showtimes["cast"],
            poster=self.movie_showtimes["poster"],
            plot=self.movie_showtimes["plot"],
            date=self.movie_showtimes["date"],
        )

    def _set_title_info(self, title="", duration="", mpaa="", genre="", studio="", director="", cast="", poster="", plot="", date="", address="", phone=""):
        # reset list
        self.getControl(100).reset()
        # set a searching message
        self.getControl(100).addItem(self.Addon.getLocalizedString(30821))
        # grab the window
        wId = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
        # set our info
        wId.setProperty("Title", title)
        wId.setProperty("Duration", duration)
        wId.setProperty("MPAA", mpaa)
        wId.setProperty("Genre", genre)
        wId.setProperty("Studio", studio)
        wId.setProperty("Director", director)
        wId.setProperty("Cast", cast)
        wId.setProperty("Poster", poster)
        wId.setProperty("Plot", plot)
        wId.setProperty("Location", self.settings["showtimes_location"])
        wId.setProperty("Date", date)
        wId.setProperty("Address", address)
        wId.setProperty("Phone", phone)

    def _get_settings(self):
        # get the users preferences
        self.settings = {
            "showtimes_location": self.Addon.getSetting("showtimes_location"),
            "showtimes_scraper": self.Addon.getSetting("showtimes_scraper"),
            "showtimes_scraper_day": self.Addon.getSetting("showtimes_scraper_day"),
            "showtimes_scraper_fallback_list_type": ["theater", "movie"][int(self.Addon.getSetting("showtimes_scraper_fallback_list_type"))],
            "date_format": xbmc.getRegion("datelong")
        }

    def _get_scraper(self):
        # get the users scraper preference
        exec "import resources.scrapers.showtimes.%s as showtimesScraper" % (self.settings["showtimes_scraper"].replace(" - ", "_").replace(" ", "_").lower(),)
        self.ShowtimesFetcher = showtimesScraper.ShowtimesFetcher(self.settings["showtimes_location"], self.settings["showtimes_scraper_fallback_list_type"])

    def _get_showtimes(self, movie=None, day="0"):
        # fetch movie showtime info
        self.movie_showtimes = self.ShowtimesFetcher.get_showtimes(movie, day)
        # create date
        try:
            date = datetime.date.today() + datetime.timedelta(days=int(self.movie_showtimes["day"]))
            self.movie_showtimes["date"] = date.strftime(self.settings["date_format"])
        except:
            self.movie_showtimes["date"] = self.movie_showtimes["day"]
        # no info found: should only happen if an error occurred
        if (self.movie_showtimes is not None and self.movie_showtimes.has_key("title")):
            self.params["showtimes"] = self.movie_showtimes["title"]
            self._set_title_info(
                title=self.movie_showtimes["title"],
                duration=self.movie_showtimes["duration"],
                mpaa=self.movie_showtimes["mpaa"],
                genre=self.movie_showtimes["genre"],
                #studio=self.movie_showtimes["studio"],
                director=self.movie_showtimes["director"],
                cast=self.movie_showtimes["cast"],
                poster=self.movie_showtimes["poster"],
                plot=self.movie_showtimes["plot"],
                date=self.movie_showtimes["date"],
            )
        # fill our list
        self._fill_list()

    def _get_selection(self, choice):
        # reset our list container
        self.getControl(100).reset()
        # add a searching message
        self.getControl(100).addItem(self.Addon.getLocalizedString(30821))
        # set our info
        if ("tid=" in self.movie_showtimes["theaters"][choice][4]):
            self.params["showtimes"] = self.movie_showtimes["theaters"][choice][0]
            self._set_title_info(
                title=self.movie_showtimes["theaters"][choice][0],
                address=self.movie_showtimes["theaters"][choice][1],
                phone=self.movie_showtimes["theaters"][choice][3],
                date=self.movie_showtimes["date"],
            )
        # get the users selection
        self._get_showtimes(self.movie_showtimes["theaters"][choice][4], self.movie_showtimes["day"])

    def _fill_list(self):
        # TODO: do we want a static list and just use window properties?
        # reset our list container
        self.getControl(100).reset()
        if (self.movie_showtimes is not None and self.movie_showtimes["theaters"]):
            # enumerate thru and add our items
            for theater in self.movie_showtimes["theaters"]:
                list_item = xbmcgui.ListItem(theater[0])
                list_item.setProperty("Address", theater[1])
                list_item.setProperty("ShowTimes", theater[2] or self.Addon.getLocalizedString(30820) % (self.params["showtimes"],))
                list_item.setProperty("Phone", theater[3])
                self.getControl(100).addItem(list_item)
        else:
            # an error in the scraper ocurred, inform user
            self.getControl(100).addItem(self.Addon.getLocalizedString(30824))

    def _close_dialog(self):
        self.close()

ui = GUI(XML_WINDOW, Addon.getAddonInfo("Path"), "default", "720p", addon=XBMCAddon())
del ui

