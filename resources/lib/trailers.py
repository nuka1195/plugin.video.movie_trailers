#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Trailers Module: List trailers and categories

from MediaWindow import DirectoryItem, MediaWindow
from database import Database
from functions import format_date, get_refresh, today
from urllib import quote_plus
import os
import xbmc
import xbmcgui


class Trailers(object):
    """Trailers Class: List trailers and categories

    """

    def __init__(self, *args, **kwargs):
        # set our passed addon object
        self.m_addon = kwargs["addon"]
        # set database object
        self.m_database = Database(addon=self.m_addon)
        # setup
        self._setup()
        # get default category
        category, categories = self._set_category(
            self.m_addon.params.get("category", None)
        )
        # media window helper functions
        self.media_window = MediaWindow(
            hId=self.m_addon.params["handle"],
            addon=self.m_addon,
            content=["movies", "addoncategories"][categories],
            links=self._get_quick_links(category)
        )
        # fetch list and end directory
        self.media_window.end(
            succeeded=self._set_list(category),
            cacheToDisc=categories
        )
        # close database
        self.m_database.close()

    def _setup(self):
        # categories
        self.root_category_list = [
            u"recent: ",
            u"studio",
            u"director",
            u"writer",
            u"actor",
            u"genre",
            u"showtimes: ",
            u"hd: ",
            u"intheaters: ",
            u"comingsoon: ",
            u"downloaded: ",
            u"downloadedrecently: ",
            u"rootlist"
        ]

    def _set_category(self, category):
        search = u""
        if (self.m_addon.params.has_key("search")):
            search = u" - ({search})".format(
                search=self.m_addon.params["search"]
            )
        # if no category, get default
        if (category is None):
            # set default category
            category = self.root_category_list[
                self.m_addon.getSetting("startup.category")
            ]
            # set default subcategory
            if (self.m_addon.getSetting("startup.category") in [1, 2, 3, 4, 5] and
                self.m_addon.getSetting("startup.category.text")):
                    category = u"{category}: {subcategory}".format(
                        category=category,
                        subcategory=self.m_addon.getSetting("startup.category.text")
                    )
        # localize search category
        self.m_addon.setSetting(
            id="plugin.category",
            value=category.replace(
                u"search", self.m_addon.getLocalizedString(30730)
            ) + search
        )
        # iterate thru and localize category
        for idx, cat in enumerate(self.root_category_list):
            self.m_addon.setSetting(
                id="plugin.category",
                value=self.m_addon.getSetting("plugin.category").replace(
                    cat, self.m_addon.getLocalizedString(30111 + idx)
                )
            )

        return (
            category,
            category in
            [u"studio", u"director", u"writer", u"actor", u"genre", u"rootlist"]
        )

    def _get_quick_links(self, category):
        # set search quick link
        if (self.m_addon.getSetting("search.current.list")):
            search = u"XBMC.RunScript({addon},search={search}&category={category})".format(
                addon=self.m_addon.getAddonInfo("Id"),
                search=quote_plus(repr(self.m_addon.params.get("search", u""))),
                category=quote_plus(repr(category))
            )
        else:
            search = u"XBMC.RunScript({addon},search={search}&category=u'')".format(
                addon=self.m_addon.getAddonInfo("Id"),
                search=quote_plus(repr(self.m_addon.params.get("search", u"")))
            )
        # set universal links
        links = [
            self.m_addon.getLocalizedString(30502),
            [],
            search,
            u"XBMC.RunScript({addon},task='configure')".format(
                addon=self.m_addon.getAddonInfo("Id")
            )
        ]
        # loop thru and add preferred button
        for id_ in range(1, 6):
            # get quick link category
            category = int(self.m_addon.getSetting(u"quick.link{id}".format(id=id_)))
            # if not disabled add quick link
            if (category > 0):
                links[1] += [[
                    self.m_addon.getLocalizedString(30110 + category),
                    "Container.Update({url}?category={category},replace)".format(
                        url=self.m_addon.params["path"],
                        category=quote_plus(repr(self.root_category_list[category - 1]))
                    ),
                    None,
                    None
                ]]

        return links

    def _set_list(self, category):
        # update source if necessary FIXME: is this where we want this
        self._update_source()
        # root list
        if (category == u"rootlist"):
            ok = self._get_root_list()
        # scraper dependent lists
        else:
            # categories
            if (category in
                [u"studio", u"director", u"writer", u"actor", u"genre"]):
                    ok = self._get_categories(category)
            # trailer listing
            else:
                ok = self._get_movies(category)

        return ok

    def _update_source(self):
        # check if scraper exists and source date
        record = self.m_database.scraper(self.m_addon.getSetting("trailer.scraper"))
        # update source if no scraper info or if user preference to update on first run
        if ((record is not None and
                self.m_addon.getSetting("source.schedule.when") == 0 and
                self.m_addon.getSetting("source.last.checked") < today(format_="%Y-%m-%d") and
                get_refresh(date=record[1], expires=record[2]))
            or record is None
            ):
                print "UPDATING SOURCE................................................................"
                # set new refresh date
                self.m_addon.setSetting(
                    "source.last.checked",
                    today(format_="%Y-%m-%d")
                )
                # import preferred scraper and fetch new trailers
                exec "from resources.scrapers.trailers import {scraper} as scraper".format(
                    scraper=self.m_addon.getSetting("trailer.scraper").replace(" - ", "_").replace(" ", "_").lower()
                )
                # update source
                scraper.Scraper(self.m_addon, self.m_database).update()

    def _get_root_list(self):
        # set thumbs
        thumbs = [
            "DefaultRecentlyAddedMovies.png",
            "DefaultFolder.png",
            "DefaultFolder.png",
            "DefaultFolder.png",
            "DefaultFolder.png",
            "DefaultMusicArtists.png",
            "DefaultFolder.png",
            "DefaultMovies.png",
            "DefaultMovies.png",
            "DefaultMovies.png",
            "DefaultMovies.png",
            "DefaultRecentlyAddedMovies.png"
        ]
        # initialize out list
        categories = []
        # iterate thru and create our category list, skipping rootlist
        for idx, cat in enumerate(self.root_category_list[:-1]):
            # only include category if enabled and trailers exist for category
            if (self.m_addon.getSetting("category{idx}".format(idx=idx + 1,)) == True and self.m_database.check_category(cat) is not None):
                categories += [[self.m_addon.getLocalizedString(30111 + idx), thumbs[idx], None, quote_plus(repr(self.root_category_list[idx]))]]

        # add categories to our media list
        return self.add_categories(categories)

    def _get_categories(self, category):
        # fetch records
        records = self.m_database.get_categories(category)
        # initialize out list
        categories = []
        # iterate thru and create our category list
        for record in records:
            categories += [[record[1], u"Default{category}.png".format(category=category.title()), None, quote_plus(repr(u"{category}: {subcategory}".format(category=category, subcategory=record[1])))]]

        # add categories to our media list
        return self.add_categories(categories)

    def add_categories(self, records):
        # get our media item
        dirItem = DirectoryItem()
        # set as folder since these our virtual folders to filtered lists
        dirItem.isFolder = True
        # FIXME: queue and now playing menu items
        # universal context menu items for categories
        # #dirItem.addContextMenuItem( xbmc.getLocalizedString( 13347 ), "XBMC.Action(Queue)" )
        # #dirItem.addContextMenuItem( xbmc.getLocalizedString( 13350 ), "XBMC.ActivateWindow(10028)" )
        dirItem.addContextMenuItem(xbmc.getLocalizedString(24020), "XBMC.RunScript({addon},task='configure')".format(addon=self.m_addon.getAddonInfo("Id")))
        dirItem.addContextMenuItem(xbmc.getLocalizedString(137), u"XBMC.RunScript({addon},search={search}&category=u'')".format(addon=self.m_addon.getAddonInfo("Id"), search=quote_plus(repr(self.m_addon.params.get("search", u"")))))
        # initialize our categories list
        categories = []
        # enumerate thru and set category
        for title, icon, thumb, category in records:
            # check for cached thumb FIXME: only actors (not enabled)
            if (thumb is None or not os.path.isfile(thumb)):
                thumb = icon
            # set the URL
            dirItem.url = u"{url}?category={category}".format(url=self.m_addon.params["path"], category=category)
            # create our listitem
            dirItem.listitem = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=thumb)
            # add context menu items to listitem with replaceItems = True so only ours show
            dirItem.listitem.addContextMenuItems(dirItem.context, replaceItems=True)
            # add category to our category list
            categories += [(dirItem.url, dirItem.listitem, dirItem.isFolder,)]

        # add categories to our media list
        return self.media_window.addItems(categories)

    def _get_movies(self, category):
        # showtimes list
        if (category.startswith("showtimes:")):
            print "FETCH showtimes and set list"
            ####################
            from resources.scrapers.showtimes.googleapi import Scraper
            movies = Scraper.fetch_movies()
            return True
        else:
            # add movies to our media list
            return self.add_movies(self.m_database.get_movies(category, self.m_addon.params.get("search", None)), category)

    def add_movies(self, records, category):
        # get our media item
        dirItem = DirectoryItem()
        # FIXME: queue and now playing menu items
        # universal context menu items for trailer lists
        # #dirItem.addContextMenuItem( xbmc.getLocalizedString( 13347 ), "XBMC.Action(Queue)" )
        dirItem.addContextMenuItem(self.m_addon.getLocalizedString(30903), u"XBMC.Action(Info)")
        # #dirItem.addContextMenuItem( xbmc.getLocalizedString( 13350 ), "XBMC.ActivateWindow(10028)" )
        dirItem.addContextMenuItem(xbmc.getLocalizedString(24020), u"XBMC.RunScript({addon},task='configure')".format(addon=self.m_addon.getAddonInfo("Id")))
        #print ["PSPSPSPSPSPSPSPS", self.m_addon.params]
        dirItem.addContextMenuItem(xbmc.getLocalizedString(137), u"XBMC.RunScript({addon},search={search}&category={category})".format(addon=self.m_addon.getAddonInfo("Id"), search=quote_plus(repr(self.m_addon.params.get("search", u""))), category=quote_plus(repr([u"", category][self.m_addon.getSetting("search.current.list")]))))
        # initialize our movies list
        movies = []
        # video and audio stream details used by some skins to display flagging
        stream_details = {
            "video": {
                "Standard": {"codec": "h264", "aspect": 1.78, "width": 720, "height": 480},
                "480p": {"codec": "h264", "aspect": 1.78, "width": 720, "height": 480},
                "720p": {"codec": "h264", "aspect": 1.78, "width": 1280, "height": 720},
                "1080p": {"codec": "h264", "aspect": 1.78, "width": 1920, "height": 1080}
            },
            "audio": {
                "Standard": {"codec": "aac", "language": "en", "channels": 2},
                "480p": {"codec": "aac", "language": "en", "channels": 2},
                "720p": {"codec": "aac", "language": "en", "channels": 2},
                "1080p": {"codec": "aac", "language": "en", "channels": 2}
            }
        }
        # iterate thru and set trailer
        for movie in records:
            # set downloaded based on all trailers available
            downloaded = (
                sum([
                     tlr in movie[27] for tlr in movie[25].split(",")
                     if (movie[27] is not None)
                ]) == len(movie[25].split(","))
            )
            # set playcount based on all trailers available
            playcount = int(
                sum([
                     tlr in movie[26] for tlr in movie[25].split(",")
                     if (movie[26] is not None)
                ]) == len(movie[25].split(","))
            )

            # set URL and play parameter
            dirItem.url = u"{url}?play={id}".format(
                url=self.m_addon.params["path"],
                id=movie[0]
            )

            # Play Trailer
            context = [(
                self.m_addon.getLocalizedString(30902),
                u"XBMC.RunPlugin({url})".format(url=dirItem.url),
            )]
            # Download & Play
            if (self.m_addon.getSetting("trailer.play.mode") == 0 and
                sum([tlr in movie[27] for tlr in movie[25].split(",")
                if (movie[27] is not None)]) < len(movie[24].split(","))):
                    context += [(
                        self.m_addon.getLocalizedString(30901),
                        u"XBMC.RunPlugin({url}&download=True)".format(
                            url=dirItem.url
                        ),
                    )]
            # Check Showtimes
            context += [(
                self.m_addon.getLocalizedString(30900),
                u"XBMC.RunScript({id},showtimes={title})".format(
                    id=self.m_addon.getAddonInfo("Id"),
                    title=quote_plus(repr(movie[1].split(" | ")[0])),
                )
            )]

            # overlay
            overlay = [
                xbmcgui.ICON_OVERLAY_UNWATCHED,
                xbmcgui.ICON_OVERLAY_WATCHED
            ][playcount]

            # tagline
            tagline = [
                "",
                "In Theaters {date}".format(
                    date=format_date(movie[4])
                )
            ][movie[4] != ""]

            # year
            year = int(movie[4][: 4] or 0)

            # format duration, sum of all available trailers
            # #duration = "{0:1.0f}:{1:02.0f}".format(*divmod(movie[23], 60))#movie[15]

            # set proper date for sorting, we use downloaded date for downloaded lists
            # and release date for in theaters and coming soon lists
            if (category.startswith("downloaded")):
                date = movie[21].split(" ")[0]
            elif (category.startswith("intheaters:") or category.startswith("comingsoon:")):
                date = movie[4]
            else:
                date = movie[16]

            # set our listitem
            dirItem.listitem = xbmcgui.ListItem(
                movie[1].split(" | ")[-1],
                iconImage="DefaultVideo.png",
                thumbnailImage="{url}|User-Agent={ua}".format(
                    url=movie[11],
                    ua=quote_plus(movie[30])
                )
            )
            # set info
            dirItem.listitem.setInfo("video", {
                "Count": movie[0],
                "PlayCount": playcount,
                "SortTitle": movie[1].split(" | ")[0],
                "Title": u"{downloaded}{title}{trailers}".format(
                    downloaded=[u"", u"* "][downloaded],
                    title=movie[1].split(" | ")[-1],
                    trailers=["", " - ({trailers})".format(
                            trailers=len(movie[24].split(","))
                        )
                    ][len(movie[24].split(",")) > 1]
                ),
                "MPAA": movie[2],
                "Studio": movie[3],
                "Date": "{day}-{month}-{year}".format(
                    day=date[8 :],
                    month=date[5 : 7],
                    year=date[: 4]
                ),
                "Year": year,
                "Director": movie[6],
                "Writer": movie[7],
                "Plot": movie[8] or "No plot available",
                "Cast": movie[9].split(" / "),
                "Genre": movie[10],
                "TagLine": tagline,
                "Size": movie[17],
                "lastplayed": movie[20] or "",
                "Overlay": overlay
            })
            # set stream details
            stream_details["video"][movie[14]]["duration"] = movie[23]
            dirItem.listitem.addStreamInfo("video", stream_details["video"][movie[14]])
            dirItem.listitem.addStreamInfo("audio", stream_details["audio"][movie[14]])
            # set additional properties
            dirItem.listitem.setProperty("ReleaseDate", format_date(movie[4]))
            dirItem.listitem.setProperty("Copyright", movie[5])
            dirItem.listitem.setProperty("AvailableTrailers", movie[24].replace(",", " / "))
            ###############################################
            # dirItem.listitem.setProperty("fanart_image", self.m_addon.getSetting("fanart")[0])
            ###############################################
            # dirItem.listitem.setProperty("Poster", movie[11])
            # used for video info dialog to search on trailers not database
            # dirItem.listitem.setProperty("Addon.Actor", movie[9].split(" / ")[0])
            # dirItem.listitem.setProperty("Addon.OnClick", "XBMC.RunScript(%s,search=%s)" % (self.m_addon.getAddonInfo("Id"), quote_plus(movie[9].split(" / ")[0].encode("UTF-8")),))
            # add context menu items to listitem with replaceItems = True so only ours show
            dirItem.listitem.addContextMenuItems(dirItem.context + context, replaceItems=True)
            # add the movie to our movie list
            movies += [(dirItem.url, dirItem.listitem, dirItem.isFolder,)]

        # add movies to our media list
        return self.media_window.addItems(movies)
