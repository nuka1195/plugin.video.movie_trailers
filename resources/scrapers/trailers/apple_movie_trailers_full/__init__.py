## Trailers scraper for http://trailers.apple.com/ (full)

import os
import xbmc
import re
import time


class _Genres_Parser:
    """ parses main xml file for all genres """
    def __init__( self, helper ):
        # set our helper object
        self.helper = helper
        # compile our regex
        self.main_genres_re = re.compile( "<GotoURL target=\"main\" url=\"(/moviesxml/g/[^\"]+)\" inhibitDragging=\"false\" draggingName=\"([^\"]+)\">" )
        self.special_genres_re = re.compile( "<Include url=\"([^\"]+)\"(?:/>)?(?:></Include>)?" )

    def clear_info( self ):
        # reset all items
        self.genres = []

    def parse_source( self, xmlSource ):
        # parse main genres
        self.genres = [ [ self.helper.unescape_text( title.replace( "/", " and " ).replace( "NAME", " ".join( os.path.basename( url ).split( "_" )[ : -1 ] ).title() ) ), url ] for url, title in self.main_genres_re.findall( xmlSource ) ]
        # parse special genres
        self.genres += [ [ [ u"Exclusives", u"Newest" ][ url.startswith( "view2" ) ], "/moviesxml/h/" + url ] for url in self.special_genres_re.findall( xmlSource ) if url.startswith( "view1" ) or url.startswith( "view2" ) ]
        # sort them
        self.genres.sort()


class _Genre_Info_Parser:
    """ parses genre xml file for all movies and next xml file """
    def __init__( self, helper ):
        # set our helper object
        self.helper = helper
        # compile our regex's
        #self.main_trailers = re.compile( "<GotoURL url=\"(/moviesxml/s/.+?/index.xml)\">\s.+?<SetFontStyle normalStyle=\"textColor2\"><B>(.+?)</B></SetFontStyle>\s.+?</GotoURL>\s.+\s.+\s.+\s.+?<GotoURL url=\"([^\"]+)\">\s.+?<SetFontStyle normalStyle=\"textColor\">([^<]+)</SetFontStyle>\s.+\s.+\s.+\s.+?<SetFontStyle normalStyle=\"textColor\">([^<]+)</SetFontStyle>\s.+\s.+\s.+?<SetFontStyle normalStyle=\"textColor\">Category: (.+?)</SetFontStyle>\s.+\s.+\s.+?<SetFontStyle normalStyle=\"textColor\">([^<]+)</SetFontStyle>" )
        self.main_trailers_re = re.compile( "<GotoURL url=\"(/moviesxml/s/.+?/.+?.xml)\">\s.+?<SetFontStyle normalStyle=\"textColor2\"><B>(.+?)</B></SetFontStyle>" )
        self.view_trailers_re = re.compile( "<GotoURL url=\"(?:http://trailers.apple.com)?(/moviesxml/s/.+?/index.xml)\" inhibitDragging=\".+?\">\s.+\s.+\s.+\s.+\s.+\s.+?<b>(.+?)</b>" )
        self.current_xml_url_re = re.compile( "(.+?)([0-9]+)" )

    def clear_info( self ):
        # reset all items
        self.trailers = []
        self.next_url = None

    def parse_source( self, xmlSource, url ):
        try:
            # find next url
            parts = self.current_xml_url_re.search( os.path.basename( url ) )
            self.next_url = "%s/%s" % ( os.path.dirname( url ), re.search( "<GotoURL url=\"(%s%d.xml)\">" % ( parts.group( 1 ), int( parts.group( 2 ) ) + 1, ), xmlSource ).group( 1 ), )
        except:
            # None found so set to None
            self.next_url = None
        # parse trailers
        if ( "view1" in url or "view2" in url ):
            # parse special genre trailers
            self.trailers = [ [ self.helper.unescape_text( title ), url ] for url, title in self.view_trailers_re.findall( xmlSource ) ]
        else:
            # parse main genre trailers
            self.trailers = [ [ self.helper.unescape_text( title ), url ] for url, title in self.main_trailers_re.findall( xmlSource ) ]


class _Movie_Info_Parser:
    """ parses a trailer xml file for all movie info and next xml file """
    def __init__( self, helper, base_url ):
        # set our helper object
        self.helper = helper
        # set our base url
        self.base_url = base_url
        # compile our regex's
        self.studio_re = re.compile( "<PathElement displayName=\"([^\"]+)\"" )
        self.info_re = re.compile( "<SetFontStyle normalStyle=\"textColor\".*?>(.+?)</SetFontStyle>", re.DOTALL )
        self.trailer_urls_re = re.compile( "<key>kind</key><string>feature-movie</string><key>songName</key><string>([^<]+)</string><key>fileExtension</key><string>[^<]+</string><key>duration</key><integer>([^<]+)</integer><key>previewLength</key><integer>([^<]+)</integer><key>playlistName</key><string>[^<]+</string><key>artistName</key> <string>([^<]+)</string><key>trackNumber</key><integer>[^<]+</integer><key>discNumber</key><integer>[^<]+</integer><key>explicit</key><integer>[^<]+</integer><key>genre</key><string>[^<]+</string><key>releaseDate</key><string>([^<]+)</string><key>dateModified</key><string>([^<]+)</string><key>url</key><string>[^<]*</string><key>category</key><string>Movie Trailers</string><key>price</key><string>[^<]+</string><key>priceDisplay</key><string>[^<]+</string><key>anonymous</key><true /><key>buyParams</key><string>[^<]+</string><key>previewURL</key><string>([^<]+)</string><key>itemId</key><string>[^<]+</string><key>s</key><integer>[^<]+</integer>" )
        self.poster_re = re.compile( "<View>\s.+?<PictureView.+?url=\"(.+?)\"[^>]+></PictureView>\s[^<]+</View>" )
        self.mpaa_re = re.compile( "<!--RATING-->\s[^<]+<.+?url=\"http://trailers.apple.com/moviesxml/i/mpaa_([^\.]+).png\">" )

    def clear_info( self ):
        # reset all items
        self.studio = self.poster = self.copyright = self.plot = self.releasedate = self.mpaa = ""
        self.trailer_urls = []
        self.cast = []
        self.urls = None

    def parse_source( self, xmlSource, url, parseall ):
        # no need to re parse certain info for same movie
        try:
            # TODO: determine if we should parse all urls as some info may be missing? (index.xml should have all info though)
            if ( parseall ):
                # parse and clean studio
                self.studio = self.helper.unescape_text( self.studio_re.findall( xmlSource )[ 1 ] )
                # parse and format poster
                self.poster = self.poster_re.search( xmlSource ).group(1)
                if ( not self.poster.startswith( "http://" ) ):
                    self.poster = self.base_url + self.poster
                # parse for various info
                items = self.info_re.findall( xmlSource )
                # parse and clean copyright
                self.copyright = self.helper.unescape_text( items[ 0 ] )
                # parse and clean plot
                self.plot = self.helper.unescape_text( items[ 1 ] )
                # parse and clean in theaters date
                ##self.releasedate = items[ 2 ].split( "</b>" )[ -1 ].strip()
                try:
                    self.releasedate = "%d-%02d-%02d" % time.strptime( items[ 2 ].split( "</b>" )[ -1 ].strip().replace( "st,", "," ).replace( "nd,", "," ).replace( "rd,", "," ).replace( "th,", "," ), "%B %d, %Y" )[ : 3 ]
                except:
                    self.releasedate = items[ 2 ].split( "</b>" )[ -1 ].strip()
                # parse and clean actors
                self.cast = [ self.helper.unescape_text( actor ) for actor in items[ 4 : -1 ] ]
                # parse and set mpaa
                mpaa = self.mpaa_re.search( xmlSource )
                if ( mpaa is None ):
                    self.mpaa = "Not yet rated"
                else:
                    self.mpaa = mpaa.group( 1 )
            # parse trailer urls
            self.trailer_urls = self.trailer_urls_re.findall( xmlSource )
            # parse for other movie xml's
            try:
                if ( self.trailer_urls ):
                    title = self.trailer_urls[ 0 ][ 0 ]
                else:
                    title = "Trailer-Index"
                # regex object
                next_urls_re = re.compile( "<GotoURL target=\"main\" url=\"(/moviesxml/s/%s/.+?.xml)\" inhibitDragging=\"true\" draggingName=\"([^\"]+)\">" % ( "/".join( url.split( "/" )[ -3 : -1 ] ), ) )
                # use a dictionary to avoid duplicates
                self.urls = dict( [ title, next_url ] for next_url, title in next_urls_re.findall( xmlSource ) )
                # clean title
                self.urls[ re.sub( " \([^\)]+\)", "", title ) ] = url
                # convert back to a list TODO: maybe keep as a dict
                self.urls = list( self.urls.items() )
            except:
                # no other urls found
                self.urls = None
        except Exception, e:
            # oops, notify user what error occurred
            xbmc.log( "%s - %s" % ( str( e ), url, ), level=xbmc.LOGERROR )


class Scraper:
    """
        Main class for scraping trailers
    """
    # scraper settings
    # base url
    BASE_URL = "http://trailers.apple.com"
    BASE_SOURCE_XML_URL = BASE_URL + "/moviesxml/h/index.xml"
    # user-agent #FIXME: support platform dependant user-agents
    USERAGENT = "QuickTime/7.6.5 (qtver=7.6.5;os=Windows NT 5.1Service Pack 3)"
    # source encoding
    ENCODING = "UTF-8"
    # additional headers
    HEADERS = { "Accept": "application/xml" }
    # number of days til source expires
    EXPIRES = 3
    # number of downloads allowed per update FIXME maybe have a setting instead. don't want to hammer apple, also maybe make it MB not trailer number
    DOWNLOAD_LIMIT = 5
    # backup source when updating
    BACKUP = False

    def __init__( self, settings, database ):
        # set passed objects
        self.database = database
        # compile regex's for performance?
        self.regex_trailer_title = re.compile( "-(tvspot|tlr|tsr|fte|clip|spot|graphicnovel)(.*?)_" )
        self.regex_trailer_720p = re.compile( "(a|h)720p\.(mov|m4v)" )
        self.regex_source_date = re.compile( "<records date=\"([^\"]+)\">" )
        self.regex_movie = re.compile( "<movieinfo id=\"([^\"]+)\"><info><title>(.+?)</title><runtime>(.*?)</runtime><rating>(.*?)</rating><studio>(.*?)</studio><postdate>(.*?)</postdate><releasedate>(.*?)</releasedate><copyright>(.*?)</copyright><director>(.*?)</director><description>(.*?)</description></info>(?:<cast>(.+?)</cast>)?(?:<genre>(.+?)</genre>)?<poster><location>(.*?)</location>(?:</poster><poster>)?<xlarge>(.*?)</xlarge></poster><preview><large filesize=\"(.+?)\">(.+?)</large></preview></movieinfo>" )
        self.regex_trailer = re.compile( "<movieinfo id=\"([^\"]+)\">.+?<runtime>(.*?)</runtime>.+?<postdate>(.*?)</postdate>.+?<preview><large filesize=\"(.+?)\">(.+?)</large></preview></movieinfo>" )
        # get scraper id
        self.scraper_id, self.source_date, expires = self.database.scraper( settings[ "trailer_scraper" ], useragent=self.USERAGENT, expires=self.EXPIRES )
        # get helper class
        self.helper = Helper( settings, self.USERAGENT, self.ENCODING, self.source_date, backup=self.BACKUP, headers=self.HEADERS )
        # fetch and parse new trailers
        source_date = self._fetch_genres()
        # update database with new source date
        self.database.scraper( settings[ "trailer_scraper" ], complete=source_date != "", sourcedate=source_date )

    def _fetch_genres( self ):
        # fetch main genres source
        xmlSource = self.helper.get_source( self.BASE_SOURCE_XML_URL, skip304=False )
        # parse source and add our items
        if ( not xmlSource ): return ""
        # Parse xmlSource for videos
        parser = _Genres_Parser( helper=self.helper )
        parser.clear_info()
        parser.parse_source( xmlSource )
        # parse genre info
        genre_parser = _Genre_Info_Parser( helper=self.helper )
        movie_parser = _Movie_Info_Parser( helper=self.helper, base_url=self.BASE_URL )
        # iterate thru and parse all genres
        for gcount, [ genre_title, genre_xml_url ] in enumerate( parser.genres ):
            ## update dialog # TODO: add percentage and counts
            ##self.dialog.update( 0, genre_title )
            ##percent = int( gcount * ( float( 100 ) / len( parser.genres ) ) )
            ##xbmcgui.Window( xbmcgui.getCurrentWindowDialogId() ).getControl( 99 ).setPercent( percent )
            # fetch genres info
            genre_xml_urls, trailer_xml_urls = self._fetch_genre_info( genre_xml_url, genre_parser, genre_title )
            # if successful continue to parse movie info
            if ( trailer_xml_urls ):
                # sort urls
                trailer_xml_urls.sort()
                # insert genre record into genres table and grab id
                ##try:
                ##    idGenre = db.execute( "SELECT idGenre FROM genre WHERE genre=?", ( genre_title, ) ).fetchone()[ 0 ]
                ##    self.db.execute( "UPDATE genre SET xml_urls=?, trailer_urls=?, updated=? WHERE genre=?;", ( repr( genre_xml_urls ), repr( trailer_xml_urls ), self.helper.today(), genre_title, ) ).lastrowid
                ##except:
                ##idGenre = self.db.execute( "INSERT INTO genre (genre, xml_urls, trailer_urls, updated) VALUES (?, ?, ?, ?);", ( genre_title, repr( genre_xml_urls ), repr( trailer_xml_urls ), self.helper.today(), ) ).lastrowid
                # enumerate thru each index.xml and parse movie info
                for count, [ title, trailer_xml_url ] in enumerate( trailer_xml_urls ):
                    ##percent = int( count * ( float( 100 ) / len( trailer_xml_urls ) ) )
                    ##self.dialog.update( percent, genre_title, title )
                    # fetch movie info
                    movie_xml_urls, trailer_urls = self._fetch_movie_info( trailer_xml_url, movie_parser )
                    ## insert movie record into movies table avoiding duplicates
                    ##self.db.execute( "INSERT INTO movie (title, xml_urls, trailer_urls, poster, plot, mpaa, studio, cast, release_date, copyright, updated) SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT * FROM movie WHERE title=?);", ( title, repr( movie_xml_urls ), repr( trailer_urls ), movie_parser.poster, movie_parser.plot, movie_parser.mpaa, movie_parser.studio, repr( movie_parser.cast ), movie_parser.releasedate, movie_parser.copyright, self.helper.today(), title, ) )
                    ### grab movies id, we do it this way as lastrowid only returns the proper id if a record was inserted
                    ##idMovie = self.db.execute( "SELECT idMovie FROM movie WHERE title=?;", ( title, ) ).fetchone()[ 0 ]
                    ### insert link record into genre_link_movie table avoiding duplicates
                    ##self.db.execute( "INSERT INTO genre_link_movie (idGenre, idMovie) SELECT ?, ? WHERE NOT EXISTS (SELECT * FROM genre_link_movie WHERE (idGenre=? AND idMovie=?));", ( idGenre, idMovie, idGenre, idMovie, ) )
                    # studio
                    ##if ( movie_parser.studio is not None ):
                    ##    # insert studio record into studios table avoiding duplicates
                    ##    self.db.execute( "INSERT INTO studio (studio) SELECT ? WHERE NOT EXISTS (SELECT * FROM studio WHERE (studio=?));", ( movie_parser.studio, movie_parser.studio, ) )
                    ##    # grab studios id, we do it this way as lastrowid only returns the proper id if a record was inserted
                    ##    idStudio = self.db.execute( "SELECT idStudio FROM studio WHERE studio=?;", ( movie_parser.studio, ) ).fetchone()[ 0 ]
                    ##    # insert link record into studio_link_movie table avoiding duplicates
                    ##    self.db.execute( "INSERT INTO studio_link_movie (idStudio, idMovie) SELECT ?, ? WHERE NOT EXISTS (SELECT * FROM studio_link_movie WHERE (idStudio=? AND idMovie=?));", ( idStudio, idMovie, idStudio, idMovie, ) )
                    # iterate thru and insert actors
                    ##for actor in movie_parser.cast:
                    ##    # insert actor record into actors table avoiding duplicates
                    ##    self.db.execute( "INSERT INTO actor (actor) SELECT ? WHERE NOT EXISTS (SELECT * FROM actor WHERE (actor=?));", ( actor, actor, ) )
                    ##    # grab actors id, we do it this way as lastrowid only returns the proper id if a record was inserted
                    ##    idActor = self.db.execute( "SELECT idActor FROM actor WHERE actor=?;", ( actor, ) ).fetchone()[ 0 ]
                    ##    # insert link record into actor_link_movie table avoiding duplicates
                    ##    self.db.execute( "INSERT INTO actor_link_movie (idActor, idMovie) SELECT ?, ? WHERE NOT EXISTS (SELECT * FROM actor_link_movie WHERE (idActor=? AND idMovie=?));", ( idActor, idMovie, idActor, idMovie, ) )
                    ### we commit every 100 records
                    if ( not count % 100 ):
                        # add movies to database
                        ##self.db.commit()
                        pass
                # add movies to database
                ### final commit
                ##self.db.commit()
        # update completed status
        ##self.db.execute( "UPDATE version SET complete=?, source_date=? WHERE idVersion=1;", ( 1, self.helper.today(), ) )
        # final commit
        ##self.db.commit()        
        ###close dialog TODO: maybe just clear info since plugins use them
        ##self.dialog.close()
        # TODO: return success not just True
        return True

    def _fetch_genre_info( self, url, parser, title ):
        # initialize genre urls and trailer urls list
        genre_xml_urls = []
        trailer_xml_urls = []
        # clear info
        parser.clear_info()
        # fetch all genres xml files and parse for trailer xml files
        while url is not None:
            ## update dialog # TODO: add percentage and counts
            ##self.dialog.update( 0, title, os.path.basename( url ) )
            # fetch source
            xmlSource = self.helper.get_source( self.BASE_URL + url, refresh=self.refresh )
            # parse source
            parser.parse_source( xmlSource, url )
            # add genre's xml url
            genre_xml_urls += [ url ]
            # add trailer xml urls
            trailer_xml_urls += parser.trailers
            # set url to next_url is None if no more found
            url = parser.next_url
        # return results
        return genre_xml_urls, trailer_xml_urls

    def _fetch_movie_info( self, url, parser ):
        # initialize finished, movie urls and trailer urls list
        finished = []
        movie_xml_urls = []
        trailer_urls = []
        # clear info
        parser.clear_info()
        # fetch all movie xml files and parse for extra trailers
        while url is not None:
            # add url to our finished list
            finished += [ url ]
            # fetch source
            xmlSource = self.helper.get_source( self.BASE_URL + url, refresh=self.refresh )#####, skip304=True )
            # parse source
            if ( xmlSource ):
                parser.parse_source( xmlSource, url, parseall=len( finished )==1 )
                # other movie xml urls, we parse these for other trailers
                if ( parser.urls is not None ):
                    # iterate thru and parse for more trailer xml files
                    for title, url in parser.urls:
                        # if new add it
                        if ( title not in dict( movie_xml_urls ) ):
                            movie_xml_urls += [ [ title, url ] ]
                # add any trailer urls found
                if ( parser.trailer_urls ):
                    trailer_urls += [ parser.trailer_urls ]
            # reset url
            url = None
            # iterate thru and check urls for new one
            for title, tmpurl in movie_xml_urls:
                # if new set url
                if ( tmpurl not in finished ):
                    url = tmpurl
                    break
        # return results
        return movie_xml_urls, trailer_urls
