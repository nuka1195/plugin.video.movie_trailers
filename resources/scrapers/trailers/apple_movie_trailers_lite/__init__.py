#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Trailers Scraper Module: http://trailers.apple.com/ (QuickTime)

from resources.lib.helper import Helper
import re
import sys
import xbmc


class Scraper(object):
    """Trailers Scraper Class: http://trailers.apple.com/ (QuickTime)

    """
    # common scraper settings
    # base URL and source files
    BASE_SOURCE_XML_URL = "http://trailers.apple.com/trailers/home/xml/{file}"
    BASE_SOURCE_XML_FILES = [
        "current.xml",
        "current_480p.xml",
        "current_720p.xml"
    ]  #, "newest.xml", "newest_480p.xml", "newest_720p.xml"]
    # user-agent
    USERAGENT = [
        "QuickTime/7.6.2 (verqt=7.6.2;cpu=IA32;so=Mac 10.5.8)",
        "QuickTime/7.6.2 (qtver=7.6.2;os=Windows NT 5.1Service Pack 3)",
    ][sys.platform.startswith("win32")]
    # source encoding
    ENCODING = "UTF-8"
    # additional headers
    HEADERS = {"Accept": "application/xml"}
    # number of days till source expires
    EXPIRES = 7
    # FIXME: maybe have a setting instead, also maybe make it MB not
    # trailer number number of downloads allowed per update
    DOWNLOAD_LIMIT = 5

    def __init__(self, addon, database):
        # set passed objects
        self.database = database
        self.m_addon = addon
        # compile regex's for performance?
        self.regex_trailer_title = re.compile(
            "(?:-|_)(filmclip|tvspot|tlr|tl|tsr|fte|clip|spot|graphicnovel|trailer)(.*?)_"
        )
        self.regex_trailer_720p = re.compile("(a|h)720p\.(mov|m4v)")
        self.regex_name = re.compile("<name>(.+?)</name>")
        self.regex_source_date = re.compile("<records date=\"([^\"]+)\">")
        self.regex_movies = re.compile("<movieinfo.+?id=\"([^\"]+)\"><info><title>(.+?)</title>(?:<runtime>(.*?)</runtime>|<runtime/>)?<rating>(.*?)</rating><studio>(.*?)</studio><postdate>(.*?)</postdate>(?:<releasedate>(.*?)</releasedate>|<releasedate/>)?<copyright>(.*?)</copyright><director>(.*?)</director><description>(.*?)</description></info>(?:<cast>(.+?)</cast>)?(?:<genre>(.+?)</genre>)?<poster><location>(.*?)</location>(?:<xlarge>(.*?)</xlarge>)?</poster><preview><large filesize=\"(.+?)\">(.+?)</large></preview></movieinfo>")
        self.regex_movies_hd = re.compile("<movieinfo.+?id=\"([^\"]+)\">.+?<large filesize=\"(.+?)\">(.+?)</large></preview></movieinfo>")
        # trailer titles
        self.trailer_titles = {
            "filmclip": "Film Clip",
            "tvspot": "TV Spot",
            "tl": "Trailer",
            "tlr": "Trailer",
            "tsr": "Teaser",
            "fte": "Featurette",
            "clip": "Film Clip",
            "spot": "TV Spot",
            "graphicnovel": "Graphic Novel"
        }
        # get scraper id
        self.scraper_id, self.source_date, expires = self.database.scraper(
            scraper=self.m_addon.getSetting("trailer.scraper"),
            useragent=self.USERAGENT,
            expires=self.EXPIRES
        )
        # get helper class
        self.helper = Helper(
            addon=self.m_addon,
            useragent=self.USERAGENT,
            encoding=self.ENCODING,
            sourcedate=self.source_date,
            headers=self.HEADERS
        )

    def update(self):
        # initialize progress dialog
        self.helper.progress_dialog(message=self.m_addon.getLocalizedString(80340))
        # backup source
        self.helper.backup_source(self.source_date)
        # fetch and parse new trailers
        source_date = self._parse_xml_source(self._get_xml_source())
        # if an error occurred return
        if (source_date is None): return
        # update database with new source date
        self.database.scraper(
            self.m_addon.getSetting("trailer.scraper"),
            complete=True,
            sourcedate=source_date
        )
        # download new trailers
        self.helper.download_trailers(limit=self.DOWNLOAD_LIMIT)
        # close dialog
        self.helper.progress_dialog(count= -1)

    def _get_xml_source(self):
        # initialize our source list
        xmlSource = []
        # iterate thru and grab all XML source files
        for count, source in enumerate(self.BASE_SOURCE_XML_FILES):
            self.helper.progress_dialog(
                count=count + 1,
                total=len(self.BASE_SOURCE_XML_FILES),
                message=self.m_addon.getLocalizedString(30840)
            )
            # fetch source and add it to our list
            xmlSource += [
                self.helper.get_source(
                    self.BASE_SOURCE_XML_URL.format(file=source),
                    skip304=self.source_date is not None
                )
            ]

        return xmlSource

    def _parse_xml_source(self, xmlSource):
        # if an error occurred fetching source, skip parsing
        if (None in xmlSource):
            return None
        # source date
        source_date = self.regex_source_date.search(xmlSource[0]).group(1)
        # gather all trailer records <movieinfo>
        movies = self.regex_movies.findall(xmlSource[0])
        movies_480p = dict([id, [size, url]] for id, size, url, in
            self.regex_movies_hd.findall(xmlSource[1])
        )
        movies_720p = dict([id, [size, url]] for id, size, url, in
            self.regex_movies_hd.findall(xmlSource[2])
        )
        # log totals for regex checking
        xbmc.log(
            "Source Date: {date} (Total Movies: {total}  -  Movies Found: {found})".format(
                date=source_date,
                total=len(re.findall("<movieinfo", xmlSource[0])),
                found=len(movies)
            ),
            xbmc.LOGNOTICE
        )
        # counters
        movies_added = trailers_added = 0
        # iterate thru and add movies
        for count, movie in enumerate(movies):
            self.helper.progress_dialog(
                count=count + 1,
                total=len(movies),
                message=movie[1].strip()
            )
            # create a trailer title based on trailer URL as apple
            # does not supply one in this source
            try:
                trailer_title = " ".join(
                    self.trailer_titles.get(part, part) for part in
                        self.regex_trailer_title.search(movie[15]).groups()
                ).strip()
            except:
                # log message for further updates and set default trailer title
                xbmc.log("No trailer name could be determined, using 'Trailer'!", xbmc.LOGNOTICE)
                xbmc.log("url: {url}".format(url=movie[15]), xbmc.LOGNOTICE)
                trailer_title = "Trailer"
            # Standard
            #FIXME: remove the .replace("!", "1")
            runtime = movie[2].rjust(4, "0").replace("!", "1").replace("@", "2")
            runtime = int(runtime.split(":")[0]) * 60 + int(runtime.split(":")[-1])
            trailers = [{
                "title": trailer_title,
                "quality": "Standard",
                "runtime": runtime,
                "postdate": movie[5],
                "size": movie[14],
                "url": movie[15]
            }]
            # 480p
            if (movies_480p.has_key(movie[0])):
                size, url = movies_480p[movie[0]]
                """
                if (runtime == 0):
                    runtime = r.rjust(4, "0").replace("!", "1").replace("@", "2")
                    runtime = int(runtime.split(":")[0]) * 60 + int(runtime.split(":")[-1])
                """
                trailers += [{
                    "title": trailer_title,
                    "quality": "480p",
                    "runtime": runtime,
                    "postdate": movie[5],
                    "size": size,
                    "url": url
                }]
            # 720p and 1080p
            if (movies_720p.has_key(movie[0])):
                size, url = movies_720p[movie[0]]
                """
                runtime = runtime.rjust(4, "0").replace("!", "1").replace("@", "2")
                runtime = int(runtime.split(":")[0]) * 60 + int(runtime.split(":")[-1])
                """
                trailers += [{
                    "title": trailer_title,
                    "quality": "720p",
                    "runtime": runtime,
                    "postdate": movie[5],
                    "size": size,
                    "url": url
                }]
                trailers += [{
                    "title": trailer_title,
                    "quality": "1080p",
                    "runtime": runtime,
                    "postdate": movie[5],
                    "size": size,
                    "url": self.regex_trailer_720p.sub("h1080p.mov", url)
                }]
            # parse genres
            genres = [
                genre.strip() for genre in
                    self.regex_name.findall(
                        movie[11].replace(" and ", "</name><name>")
                    )
                if (genre)
            ]
            genres.sort()
            # add/update movie
            added = self.database.add_movie({
                "scraper": self.scraper_id,
                "title": movie[1].strip(),
                "mpaa": movie[3].strip() or "Not yet rated",
                "studio": movie[4].strip(),
                "releasedate": movie[6].strip(),
                "copyright": movie[7].strip(),
                "director": [director.strip() for director in
                    movie[8].split(",") if (director)],
                "writer": [],  # FIXME: if Apple adds writer add it
                "plot": movie[9].strip(),
                "cast": [actor.strip() for actor in
                    self.regex_name.findall(movie[10]) if (actor)],
                "genre": genres,
                "poster": movie[13].strip() or movie[12].strip(),
                "trailers": trailers
            })
            # add to our counters
            movies_added += added[0]
            trailers_added += added[1]

        # commit changes
        self.database.commit()
        # split date from time offset
        source_date, hours = source_date.rsplit(" ", 1)

        # log totals for regex checking
        xbmc.log(
            "Source Date: {date} (Total Movies: {total}  -  Movies Found: {found})".format(
                date=source_date,
                total=len(re.findall("<movieinfo", xmlSource[0])),
                found=len(movies)
            ),
            xbmc.LOGNOTICE
        )
        xbmc.log(
            "             {added} of {total} movies added.".format(
                added=movies_added,
                total=len(movies)
            ),
            xbmc.LOGNOTICE
        )
        xbmc.log(
            "             {added} of {total} trailers added.".format(
                added=trailers_added,
                total=len(movies)
            ),
            xbmc.LOGNOTICE
        )
        message = "{madded:d} movies added and {tadded:d} trailers added".format(
            madded=movies_added,
            tadded=trailers_added
        )
        self.helper.notification(message)
        # return source date
        return self.helper.format_source_date(
            "{date} GMT".format(date=source_date), -(int(hours) / 100)
        )

    def _download(self):
        # here is where if the user preference is to download new trailers we do
        pass
