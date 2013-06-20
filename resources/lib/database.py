#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Database Module: All database related functions


from functions import today, translatePath
import os
import re
import sqlite3 as sqlite
import xbmc
import xbmcvfs


class Table(object):

    def create_tables(self):
        """Creates all tables and indexes.

        """
        # version table
        self.execute("CREATE TABLE version (idVersion integer PRIMARY KEY AUTOINCREMENT, version text);")
        # download queue table
        self.execute("CREATE TABLE download_queue (idAddon text UNIQUE, queue text);")
        # scraper table
        self.execute("CREATE TABLE scraper (idScraper integer PRIMARY KEY AUTOINCREMENT, scraper text UNIQUE, useragent text, complete integer DEFAULT 0, sourcedate text, expires integer DEFAULT 7);")
        # movie table
        self.execute("CREATE TABLE movie (idMovie integer PRIMARY KEY AUTOINCREMENT, title text UNIQUE, mpaa text, studio text, releasedate text, copyright text, director text, writer text, plot text, cast text, genre text, poster text);")
        # trailer table and link tables
        self.execute("CREATE TABLE trailer (idTrailer integer PRIMARY KEY AUTOINCREMENT, title text, quality text, runtime integer, postdate text, size integer, url text UNIQUE, playcount integer, watched text, downloaded text, path text);")
        self.execute("CREATE TABLE trailer_link_scraper (idTrailer integer NOT NULL, idScraper integer NOT NULL, UNIQUE (idTrailer, idScraper) CONSTRAINT unique_idtrailer_idscraper, UNIQUE (idScraper, idTrailer) CONSTRAINT unique_idscraper_idtrailer);")
        self.execute("CREATE TABLE trailer_link_movie (idTrailer integer NOT NULL, idMovie integer NOT NULL, UNIQUE (idTrailer, idMovie) CONSTRAINT unique_idtrailer_idmovie, UNIQUE (idMovie, idTrailer) CONSTRAINT unique_idmovie_idtrailer);")
        # studio table and link table
        self.execute("CREATE TABLE studio (idStudio integer PRIMARY KEY AUTOINCREMENT, studio text UNIQUE);")
        self.execute("CREATE TABLE studio_link_movie (idStudio integer NOT NULL, idMovie integer NOT NULL, UNIQUE (idStudio, idMovie) CONSTRAINT unique_idstudio_idmovie, UNIQUE (idMovie, idStudio) CONSTRAINT unique_idmovie_idstudio);")
        # director table and link table
        self.execute("CREATE TABLE director (idDirector integer PRIMARY KEY AUTOINCREMENT, director text UNIQUE);")
        self.execute("CREATE TABLE director_link_movie (idDirector integer NOT NULL, idMovie integer NOT NULL, UNIQUE (idDirector, idMovie) CONSTRAINT unique_iddirector_idmovie, UNIQUE (idMovie, idDirector) CONSTRAINT unique_idmovie_iddirector);")
        # writer table and link table
        self.execute("CREATE TABLE writer (idWriter integer PRIMARY KEY AUTOINCREMENT, writer text UNIQUE);")
        self.execute("CREATE TABLE writer_link_movie (idWriter integer NOT NULL, idMovie integer NOT NULL, UNIQUE (idWriter, idMovie) CONSTRAINT unique_idwriter_idmovie, UNIQUE (idMovie, idWriter) CONSTRAINT unique_idmovie_idwriter);")
        # actor table and link table
        self.execute("CREATE TABLE actor (idActor integer PRIMARY KEY AUTOINCREMENT, actor text UNIQUE);")
        self.execute("CREATE TABLE actor_link_movie (idActor integer NOT NULL, idMovie integer NOT NULL, UNIQUE (idActor, idMovie) CONSTRAINT unique_idactor_idmovie, UNIQUE (idMovie, idActor) CONSTRAINT unique_idmovie_idactor);")
        # genre table and link table
        self.execute("CREATE TABLE genre (idGenre integer PRIMARY KEY AUTOINCREMENT, genre text UNIQUE);")
        self.execute("CREATE TABLE genre_link_movie (idGenre integer NOT NULL, idMovie integer NOT NULL, UNIQUE (idGenre, idMovie) CONSTRAINT unique_idgenre_idmovie, UNIQUE (idMovie, idGenre) CONSTRAINT unique_idmovie_idgenre);")
        # FIXME: these don't work correctly unless all id's are in the INSERT ON table
        # add triggers
        # self.execute("""
        #    CREATE TRIGGER add_trailer
        #        AFTER INSERT ON trailer
        #            BEGIN
        #                INSERT INTO trailer_link_movie (idTrailer, idMovie) VALUES (new.idTrailer, new.idMovie);
        #                INSERT INTO trailer_link_scraper (idTrailer, idScraper) VALUES (new.idTrailer, new.idScraper);
        #            END;
        # """)
        # self.execute("""
        #    CREATE TRIGGER add_actor
        #        AFTER INSERT ON actor
        #            BEGIN
        #                INSERT INTO actor_link_movie (idActor, idMovie) VALUES (new.idActor, new.idMovie);
        #            END;
        # """)
        # insert version
        self.execute("INSERT INTO version (version) VALUES (?);", (self.m_addon.getAddonInfo("version"),))
        # commit changes
        self.commit()

        # return addon version
        return self.m_addon.getAddonInfo("version")


class Scraper(object):
    def scraper(self, scraper, **kwargs):
        """
            Gets and/or sets scraper info.
        """
        # grab scrapers id
        idScraper = self.execute("SELECT idScraper, sourcedate, expires FROM scraper WHERE scraper=?;", (scraper,)).fetchone()
        # insert/update scraper info
        if (idScraper is None and kwargs.has_key("useragent")):
            idScraper = [self.execute("INSERT INTO scraper (scraper, useragent, expires) VALUES (?, ?, ?);", (scraper, kwargs.get("useragent", ""), kwargs.get("expires", 7),)).lastrowid, None, None]
            self.commit()
        elif (idScraper is not None and kwargs.has_key("complete")):
            self.execute("UPDATE scraper SET complete=?, sourcedate=? WHERE idScraper=?;", (int(kwargs.get("complete", 0)), kwargs.get("sourcedate", today()), idScraper[0],))
            self.commit()

        return idScraper


class Category(object):

    def check_category(self, category):
        """
            Used for category list to prevent categories with no result.
        """
        # main categories
        if (category in [u"studio", u"director", u"writer", u"actor", u"genre"]):
            return self.execute("SELECT * FROM {category}_link_movie LIMIT 1;".format(category=category)).fetchone()
        # any downloaded?
        elif (category.startswith(u"downloaded")):
            return self.execute("SELECT * FROM trailer WHERE downloaded IS NOT NULL LIMIT 1;").fetchone()
        # any HD?
        elif (category.startswith(u"hd: ")):
            return self.execute("SELECT * FROM trailer WHERE trailer.quality IN ('720p','1080p') LIMIT 1;").fetchone()
        # all other just return True
        else:
            return True

    def get_categories(self, category):
        """
            Returns a list of categories. (studios, directors, writers, actors, genres )
        """
        # return records
        return self.execute("SELECT * FROM {category};".format(category=category)).fetchall()


class Trailer(object):
    """Handles all methods relating to trailers"""

    def mark_trailer_watched(self, trailer, clear=False):
        # set info
        info = {
            "playcount": [(trailer[7] or 0) + 1, None][clear],
            "watched": [today(), None][clear]
        }

        self.mark_trailer(trailer[0], info)

    def mark_trailer_downloaded(self, trailer, clear=False):
        # set info
        info = {
            "downloaded": [today(), None][clear],
            "path": [trailer[10], None][clear]
        }
        # only add size if we're not clearing status
        if (not clear):
            info.update({"size": trailer[5]})

        self.mark_trailer(trailer[0], info)

    def mark_trailer(self, trailer, info):
        # update record
        self.update_record(
            table="trailer",
            key_name="idTrailer",
            key_value=trailer,
            info=info
        )
        self.commit()

    def get_trailers(self, idMovie, hd=False, downloaded=False):
        """Returns trailers available for a specific movie.

        """
        # set SQL, only need HD and downloaded Limits, MPAA and genres not necessary as the movie is in the list
        sql = """
            SELECT trailer.*, scraper.*, movie.*
            FROM movie, trailer, scraper, trailer_link_movie, trailer_link_scraper
            WHERE trailer_link_movie.idMovie=?
            AND trailer.idTrailer=trailer_link_movie.idTrailer
            AND movie.idMovie=trailer_link_movie.idMovie
            AND trailer.idTrailer=trailer_link_scraper.idTrailer
            AND scraper.idScraper=trailer_link_scraper.idScraper
            {limits[0]}
            {limits[2]};
        """.format(limits=self._get_limits(hd=hd, downloaded=downloaded))  # ORDER BY trailer.postdate

        return self.execute(sql, (idMovie,)).fetchall()


class Movie(Trailer):
    """Movie Class: All methods related to movies"""
    #def get_movie(self, idMovie):
    #    """Returns a movies details."""
    #
    #    # return movie details
    #    return self.execute("SELECT * FROM movie WHERE idMovie=? LIMIT 1;", (idMovie,)).fetchone()

    def get_downloaded(self):
        """returns all movies where a trailer has a downloaded date"""

        return self.get_movies(category="downloaded")

    def get_movies(self, category, search=None):
        """Returns a list of movies."""

        # initialize these as they don't apply to all lists
        tables = category_sql = orderby_sql = ""
        params = None
        # recent
        if (category.startswith("recent:")):
            params = (30,)
            orderby_sql = "ORDER BY trailer.postdate DESC LIMIT ?"  # trailer.idTrailer
        # downloaded
        elif (category.startswith("downloaded")):
            # only recent categories require order by and params
            if (category.startswith("downloadedrecently:")):
                params = (30,)
                orderby_sql = "ORDER BY trailer.downloaded DESC LIMIT ?"
        # release date based
        elif (category.startswith("intheaters:") or category.startswith("comingsoon:")):
            params = (today(days=[-60, 1][category.startswith("comingsoon:")], format_="%Y-%m-%d"), today(days=[0, 365][category.startswith("comingsoon:")], format_="%Y-%m-%d"),)
            category_sql = "AND ({soon}releasedate BETWEEN ? AND ?)".format(soon=["", "releasedate='Coming Soon' OR "][category.startswith("comingsoon:")])
        # all other
        elif (category != "" and not category.startswith("hd:")):
            kind, subcat = category.split(": ")
            params = (subcat,)
            tables = ", {kind}, {kind}_link_movie".format(kind=kind)
            category_sql = "AND {kind}_link_movie.idMovie=movie.idMovie AND {kind}_link_movie.id{kind}={kind}.id{kind} AND {kind}.{kind}=?".format(kind=kind)

        # search
        if (search is not None):
            # need to make sure params is not None since we add to it
            if (params is None): params = ()

            # loop thru and add each search
            # should only be multiple if user preference is to search current list
            for s in search.split(" - "):
                # order by param needs to be last
                if (orderby_sql != ""):
                    params = (self._get_regex_pattern(s),) + params
                else:
                    params += (self._get_regex_pattern(s),)
                # add search SQL
                category_sql += "\nAND ((movie.title || ' ' || movie.studio || ' ' || movie.director || ' ' || movie.writer || ' ' || movie.plot || ' ' || movie.cast || ' ' || movie.genre) REGEXP ?)"

        # get Quality and MPAA rating limits SQL and format SQL
        sql = """
            SELECT movie.*, trailer.*,
            SUM(trailer.runtime),
            GROUP_CONCAT(DISTINCT trailer.title),
            GROUP_CONCAT(DISTINCT trailer.url),
            GROUP_CONCAT(DISTINCT trailer.url || '|' || trailer.watched),
            GROUP_CONCAT(DISTINCT trailer.url || '|' || trailer.downloaded),
            scraper.*
            FROM movie, trailer, scraper, trailer_link_movie, trailer_link_scraper{tables}
            WHERE movie.idMovie=trailer_link_movie.idMovie
            AND trailer.idTrailer=trailer_link_movie.idTrailer
            AND trailer.idTrailer=trailer_link_scraper.idTrailer
            AND scraper.idScraper=trailer_link_scraper.idScraper
            {category}
            {limits[0]}
            {limits[1]}
            {limits[2]}
            GROUP BY trailer_link_movie.idMovie
            {orderby};
        """.format(
                tables=tables,
                category=category_sql,
                limits=self._get_limits(
                    hd=category.startswith("hd:"),
                    downloaded=category.startswith("downloaded"),
                ),
                orderby=orderby_sql
            )
        print sql
        # fetch records
        if (params is None):
            return self.execute(sql)
        else:
            return self._highlight_search_results(self.execute(sql, params), search)

    # FIXME: this may not work with multiple searches? TEST
    def _highlight_search_results(self, records, search):
        """Highlights search matches. (Requires skin support.)"""

        # no highlight required
        if (self.m_addon.getSetting("search.highlight.color") is None or search is None):
            return records
        # compile REGEX for performance?
        regex_search_pattern = re.compile(self._get_regex_pattern(search, highlight=True), re.IGNORECASE)
        # initialize our final results list
        movies = []
        # iterate thru and highlight search results
        for record in records:
            movies += [[
                record[0],
                u"{sorttitle} | {title}".format(
                    sorttitle=record[1],
                    title=regex_search_pattern.sub("[COLOR {color}]\\1[/COLOR]".format(
                            color=self.m_addon.getSetting("search.highlight.color")),
                            record[1]
                        )
                    ),
                    record[2],
                    regex_search_pattern.sub("[COLOR {color}]\\1[/COLOR]".format(
                        color=self.m_addon.getSetting("search.highlight.color")),
                        record[3]
                    ),
                    record[4],
                    record[5],
                    regex_search_pattern.sub("[COLOR {color}]\\1[/COLOR]".format(
                        color=self.m_addon.getSetting("search.highlight.color")),
                        record[6]
                    ),
                    regex_search_pattern.sub("[COLOR {color}]\\1[/COLOR]".format(
                        color=self.m_addon.getSetting("search.highlight.color")),
                        record[7]
                    ),
                    regex_search_pattern.sub("[COLOR {color}]\\1[/COLOR]".format(
                        color=self.m_addon.getSetting("search.highlight.color")),
                        record[8]
                    ),
                    regex_search_pattern.sub("[COLOR {color}]\\1[/COLOR]".format(
                        color=self.m_addon.getSetting("search.highlight.color")),
                        record[9]
                    ),
                    regex_search_pattern.sub("[COLOR {color}]\\1[/COLOR]".format(
                        color=self.m_addon.getSetting("search.highlight.color")),
                        record[10]
                    )
                ] + list(record[11 :])
            ]

        # return results with highlighted text
        return movies

    def unhighlight_text(self, text):
        # return text with any highlighting removed
        return self.regex_unhighlight_text.sub("", text)

    def _get_regex_pattern(self, search, highlight=False):
        # whole words only?
        whole_words = ["", "\\b"][self.m_addon.getSetting("search.whole.words")]
        # match exact phrase
        if (self.m_addon.getSetting("search.type") == 2):
            return "\\b({search})\\b".format(search=search)
        # match any word, if we are highlighting we want this pattern for all words also
        elif (self.m_addon.getSetting("search.type") == 0 or highlight):
            return "{wholewords}({search}){wholewords}".format(wholewords=whole_words, search="|".join([word for word in search.split()]))
        # match all words
        else:
            return "|".join(["{wholewords}{word}{wholewords}".format(wholewords=whole_words, word=word) for word in search.split()])

    def _get_limits(self, hd=True, downloaded=False):  #, mpaa="", genres=""):
        """
            Sets SQL limits for Quality, MPAA, Downloaded trailers and Genres.
        """
        #print ["LIMITS", hd, downloaded, mpaa, genres]
        # qualities available
        qualities = ["Standard", "480p", "720p", "1080p"][2 * (hd or (self.m_addon.getSetting("trailer.hd.only"))) : [["Standard", "480p", "720p", "1080p"].index(self.m_addon.getSetting("trailer.quality")) + 1, 5][hd]]
        # add all up to the preferred quality, leave blank if 1080p and not HD only
        quality_sql = ["AND trailer.quality IN ('{limits}')".format(limits="','".join([quality for quality in qualities])), ""][self.m_addon.getSetting("trailer.quality") == "1080p" and not self.m_addon.getSetting("trailer.hd.only") and not hd]
        # add all up to the preferred MPAA rating, leave blank if no limit
        mpaa_ratings = ["NR", "Not yet rated", "G", "PG", "PG-13", "R", "NC-17"]
        #if (mpaa != ""):
        #    mpaa = mpaa_ratings.index(mpaa)
        #else:
        mpaa = self.m_addon.getSetting("trailer.limit.mpaa") + 2
        mpaa_sql = ["AND movie.mpaa IN ('{limits}')".format(limits="','".join([rating for rating in mpaa_ratings[2 * (self.m_addon.getSetting("trailer.nr.mpaa") > mpaa - 2) : mpaa + 1]])), ""][mpaa == 6]
        # set downloaded only SQL, leave blank for all videos
        downloaded_sql = ["AND trailer.downloaded IS NOT NULL", ""][not downloaded]
        # add all genres, leave blank for all genres
        #genre_sql = ["AND ({limits})".format(limits=" OR ".join(["movie.genre LIKE '%{genre}%'".format(genre=genre) for genre in genres.split(" / ")])), ""][genres == ""]

        return quality_sql, mpaa_sql, downloaded_sql  #, genre_sql

    def add_movie(self, record):
        """Adds a movie to the database"""
        # FIXME: maybe check for missing info and update record
        # grab idMovie, we do it this way as lastrowid only returns the proper id if a record was inserted not updated
        idMovie = self.execute("SELECT idMovie FROM movie WHERE LOWER(title)=?;", (record["title"].lower(),)).fetchone()
        # set message
        msg = ["Skipping", "Adding"][idMovie is None]

        movie_added = False
        # if no id then we insert a new record
        if (idMovie is None):
            movie_added = True
            # insert movie record and get id
            idMovie = [self.execute("INSERT INTO movie (title, mpaa, studio, releasedate, copyright, director, writer, plot, cast, genre, poster) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (record["title"], record["mpaa"], record["studio"], record["releasedate"], record["copyright"], " / ".join(record["director"]), " / ".join(record["writer"]), record["plot"], " / ".join(record["cast"]), " / ".join(record["genre"]), record["poster"],)).lastrowid]
            # studio
            if (record["studio"]):
                # grab idStudio, we do it this way as lastrowid only returns the proper id if a record was inserted
                idStudio = self.execute("SELECT idStudio FROM studio WHERE studio=?;", (record["studio"],)).fetchone()
                # insert studio record and get id
                if (idStudio is None):
                    idStudio = [self.execute("INSERT INTO studio (studio) VALUES (?);", (record["studio"],)).lastrowid]
                # insert link record into studio_link_movie table
                self.execute("INSERT OR IGNORE INTO studio_link_movie (idStudio, idMovie) VALUES (?, ?);", (idStudio[0], idMovie[0],))
            # iterate thru and insert directors
            for director in record["director"]:
                # grab idDirector, we do it this way as lastrowid only returns the proper id if a record was inserted
                idDirector = self.execute("SELECT idDirector FROM director WHERE director=?;", (director,)).fetchone()
                # insert director record and get id
                if (idDirector is None):
                    idDirector = [self.execute("INSERT INTO director (director) VALUES (?);", (director,)).lastrowid]
                # insert link record into director_link_movie table
                self.execute("INSERT OR IGNORE INTO director_link_movie (idDirector, idMovie) VALUES (?, ?);", (idDirector[0], idMovie[0],))
            # iterate thru and insert writers
            for writer in record["writer"]:
                # grab idWriter, we do it this way as lastrowid only returns the proper id if a record was inserted
                idWriter = self.execute("SELECT idWriter FROM writer WHERE writer=?;", (writer,)).fetchone()
                # insert writer record and get id
                if (idWriter is None):
                    idWriter = [self.execute("INSERT INTO writer (writer) VALUES (?);", (writer,)).lastrowid]
                # insert link record into writer_link_movie table
                self.execute("INSERT OR IGNORE INTO writer_link_movie (idWriter, idMovie) VALUES (?, ?);", (idWriter[0], idMovie[0],))
            # iterate thru and insert actors
            for actor in record["cast"]:
                # grab idActor, we do it this way as lastrowid only returns the proper id if a record was inserted
                idActor = self.execute("SELECT idActor FROM actor WHERE actor=?;", (actor,)).fetchone()
                # insert actor record and get id
                if (idActor is None):
                    idActor = [self.execute("INSERT INTO actor (actor) VALUES (?);", (actor,)).lastrowid]
                # insert link record into actor_link_movie table
                self.execute("INSERT OR IGNORE INTO actor_link_movie (idActor, idMovie) VALUES (?, ?);", (idActor[0], idMovie[0],))
            # iterate thru and insert genres
            for genre in record["genre"]:
                # grab idGenre, we do it this way as lastrowid only returns the proper id if a record was inserted
                idGenre = self.execute("SELECT idGenre FROM genre WHERE genre=?;", (genre,)).fetchone()
                # insert genre record and get id
                if (idGenre is None):
                    idGenre = [self.execute("INSERT INTO genre (genre) VALUES (?);", (genre,)).lastrowid]
                # insert link record into genre_link_movie table
                self.execute("INSERT OR IGNORE INTO genre_link_movie (idGenre, idMovie) VALUES (?, ?);", (idGenre[0], idMovie[0],))
        # log action
        xbmc.log("{msg} Movie {movie!r}...".format(
                msg=msg,
                movie=record["title"].encode("UTF-8")
            ),
            xbmc.LOGNOTICE
        )

        trailer_added = False
        # iterate thru and insert trailers
        for trailer in record["trailers"]:
            # grab idTrailer, we do it this way as lastrowid only returns
            # the proper id if a record was inserted
            idTrailer = self.execute("SELECT idTrailer FROM trailer WHERE url=?;",
                (trailer["url"],)
            ).fetchone()
            # set message
            msg = ["Skipping {trailer!r}", "Adding {trailer!r}"][idTrailer is None]
            # insert trailer record and get id
            if (idTrailer is None):
                trailer_added = True
                idTrailer = self.execute(
                    "INSERT INTO trailer (title, quality, runtime, postdate, size, url) VALUES (?, ?, ?, ?, ?, ?);",
                    (
                        trailer["title"],
                        trailer["quality"],
                        trailer["runtime"],
                        trailer["postdate"],
                        trailer["size"],
                        trailer["url"],
                    )
                ).lastrowid
                # insert link records into trailer_link_movie and trailer_link_scraper tables
                self.execute("INSERT OR IGNORE INTO trailer_link_movie (idTrailer, idMovie) VALUES (?, ?);",
                    (idTrailer, idMovie[0],)
                )
                self.execute("INSERT OR IGNORE INTO trailer_link_scraper (idTrailer, idScraper) VALUES (?, ?);",
                    (idTrailer, record["scraper"],)
                )
            # log action
            xbmc.log("{msg: <25} quality: {quality: <12}  url: {url!r}".format(
                    msg=msg.format(trailer=trailer["title"].encode("UTF-8")),
                    quality="({quality})".format(quality=trailer["quality"]),
                    url=trailer["url"].encode("UTF-8")
                ),
                xbmc.LOGNOTICE
            )

        return [movie_added, trailer_added]

class Database(Table, Category, Movie, Scraper):
    """Database Class: All database related functions.
                       All scrapers use the same database.

    """
    def __init__(self, *args, **kwargs):
        # initialize xbmcaddon module
        Table.__init__(self)  #, sys.modules["__main__"].ADDON_ID)
        # unhighlight regex
        self.regex_unhighlight_text = re.compile("\[COLOR .+?\]|\[/COLOR\]")
        # set addon object
        self.m_addon = kwargs["addon"]
        # connect to database FIXME: here is where we would update DB if needed
        version = self.connect()

    def connect(self):
        # if the path to the database does not exist create it
        if (not xbmcvfs.mkdirs(self.m_addon.getSetting("source.cache.path"))):
            raise IOError(
                1,
                "Unable to make dir structure!",
                self.m_addon.getSetting("source.cache.path")
            )
        # set DB object
        self.m_database = sqlite.connect(
            translatePath(os.path.join(
                self.m_addon.getSetting("source.cache.path"),
                u"trailers.db"
            ))
        )
        # used for searching
        self.m_database.create_function("regexp", 2, self.regexp)
        # create DB if doesn't exists
        return self._get_version()

    def regexp(self, pattern, item):
        """Regex function for searching.

        """
        # all words search
        if (self.m_addon.getSetting("search.type") == 1):
            return sum([re.search(p, item, re.IGNORECASE) is not None
                for p in pattern.split("|")]) == len(pattern.split("|"))
        # any word or exact phrase search
        return re.search(pattern, item, re.IGNORECASE) is not None

    def execute(self, sql, args=None):
        # execute the SQL command
        if (args is not None):
            return self.m_database.execute(sql, args)
        else:
            return self.m_database.execute(sql)

    def commit(self):
        # commit transactions
        try:
            self.m_database.commit()
        except Exception as e:
            print e

    def close(self):
        # close DB
        self.m_database.close()

    def _get_version(self):
        """Returns the version of Movie Trailers addon the DB was created with.
           Creates the database if no version was retrieved.

        """
        try:
            return self.execute("SELECT version FROM version;").fetchone()
        except:
            return self.create_tables()

    def update_record(self, table, key_name, key_value, info):
        """Updates a record with passed info."""

        # set columns and params
        columns = ", ".join(["{column}=?".format(column=key) for key in info.keys()])
        params = tuple(info.values() + [key_value])
        # update trailer
        self.execute(
            "UPDATE {table} SET {columns} WHERE {key}=?;".format(
                table=table,
                columns=columns,
                key=key_name
            ),
            params
        )

    def get_xbmc_library_path(self, title):
        """Searches xbmc library for a match of title.
           Used for saving trailers with movies.

        """
        # JSON equivalents to Python
        #null = None
        #false = False
        #true = True
        # set JSON command to retrieve path of movie if found
        command = str({
            "jsonrpc": "2.0",
            "method": "VideoLibrary.GetMovies",
            "id": str(self.m_addon.getAddonInfo("id")),
            "params": {
                "filter": {
                    "field": "title",
                    "operator": "is",
                    "value": str(title).replace("'", "&apos;")
                },
                "properties" : ["file"],
            }
        }).replace("'", "\"").replace("&apos;", "'")  # replace is necessary, otherwise we get parse errors
        print command
        # get response
        response = xbmc.executeJSONRPC(command)
        print response
        # eval() response to a python dict() and return file path
        # startswith is a safety check.
        if (response.startswith("{")):
            return eval(response)["result"].get(
                "movies", [{"file": None}]
            )[0]["file"]

        # not a valid JSON object
        return None

    def queue(self, addon_id, item=None):
        # grab queue
        queue = self.execute(
            "SELECT * FROM download_queue WHERE idAddon=?;",
            (addon_id,)
        ).fetchone()
        # set queue
        queue = queue or (addon_id, "[]",)
        queue = eval(queue[1])
        # append/delete item
        if (isinstance(item, int)):
            queue.pop(item)
        elif (item):
            queue.append(item)
        # update queue and commit
        self.execute(
            "INSERT OR REPLACE INTO download_queue (idAddon, queue) VALUES (?, ?);",
            (addon_id, repr(queue),)
        )
        self.commit()

        # return the queue
        return queue
