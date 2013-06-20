""" Scraper for http://www.google.com/movies """
##########################FIX THEATER?MOVIE LIST
import os

try:
    # our we debugging?
    import xbmc
    DEBUG = False
except:
    DEBUG = True

import urllib
import urllib2
import re

__title__ = "Google"
__credit__ = "Nuka1195"


class _ShowtimesParser:
    """ Parser Class: parses an html document for movie showtimes """

    # base url
    BASE_URL = "http://www.google.com"

    def __init__(self, source, movie=None, day="0", theaterlist=None):
        # initialize our variable
        self.showtimes = {"day": day}
        # parse source
        self._parse(source, movie, theaterlist)

    def _parse(self, source, movie, theaterlist):
        # regex for finding future dates
        pattern_nextdate = "<a href=\"(/movies\?near=.+?date=([^&]+)[^\"]+)\">[^<]+</a>"
        ## IN SVN Good for US only
        ##pattern_movieinfo = "<img src=\"(/movies/image\?tbn=[a-z0-9]+&amp;size=[0-9]+x[0-9]+)+\".+?<span dir=ltr>([^<]+)</span>.+?<div class=info>Director: ([^<]+)<br>Cast: ([^<]+)<br>(?:.+?)?([0-9]+hr[^-]+)- (?:Rated ([^]+) - )?([^<]+)</div><div class=syn>(.+?)&laquo; less"#<span id=LessAfterSynopsisSecond0 style=\"display:none\">"
        pattern_movieinfo = "(?:<img src=\"(/movies/image\?tbn=[a-z0-9]+&amp;size=[0-9]+x[0-9]+)+\".+?)?<span dir=ltr>([^<]+)</span>.+?<div class=info>(?:.+?<div class=info>Director: ([^<]+))?(?:<br>)?(?:<br><nobr><nobr>)?(?:Cast: ([^<]+)<br>)?(?:.+?)?([0-9]+hr[^-]+)- (?:(Rated [^]+) - )?([^<]+)</div>(?:<div class=syn>(.+?)&laquo; less)?"
        pattern_movieinfo = "<img src=\"(/movies/image\?tbn=[a-z0-9]+&amp;size=[0-9]+x[0-9]+)\".*?<span dir=ltr>([^<]+).*?<div class=info>([^<]+)<.*?<br>Director: (.+?)Cast: ([^<]+)<.+?<div class=syn>(.+?)&laquo; less"

        # regex for scraping theater and movie lists
        """
        #pattern_theaterinfo = "<%s class=name><a href=\"(/movies\?near=[^\"]+)\"[^<]+<span dir=ltr>([^<]+)</span></a></%s><[^>]+>(?:<nobr><nobr>.+?</nobr></nobr>)?([^<]+).+?<div class=[^>]+>(.+?)</div>"
        pattern_theaterinfo = "<%s class=name><a href=\"(/movies\?near=[^\"]+)\"[^<]+<span dir=ltr>([^<]+)</span></a></%s><[^>]+>(?:<nobr><nobr>.+?</nobr></nobr>)?([^<]+).+?<div class=[^>]+>(.+?)</div>"
        <div class=theater><div id=theater_6750433078994449928 ><div class=name><a href="/movies?near=48161&amp;hl=en&amp;date=0&amp;tid=5dae5b1eb982b608" id=link_1_theater_6750433078994449928>Phoenix Theatres The Mall of Monroe</a></div><div class=address>2121 N. Monroe St., Monroe, MI<a href="" class=fl target=_top></a></div></div><div class=times>10:45am&nbsp; 1:15&nbsp; 3:40&nbsp; 6:10&nbsp; 8:40&nbsp; 10:50pm</div></div>

<div class=theater><div id=theater_11106351332624381742 ><div class=name><a href="/movies?near=48161&amp;hl=en&amp;date=0&amp;tid=9a21afb16bc3372e" id=link_1_theater_11106351332624381742>Emagine Woodhaven</a></div><div class=address>21720 Allen Rd., Woodhaven, MI<a href="" class=fl target=_top></a></div></div><div class=times>11:00am&nbsp; 1:35&nbsp; 4:10&nbsp; 7:05&nbsp; 9:50pm</div></div>

<div class=theater><div id=theater_16900464372677607732 ><div class=name><a href="/movies?near=48161&amp;hl=en&amp;date=0&amp;tid=ea8a82cdf0980134" id=link_1_theater_16900464372677607732>Spotlight Taylor 10</a></div><div class=address>22265 Eureka Rd., Taylor, MI<a href="" class=fl target=_top></a></div></div><div class=times>12:50&nbsp; 4:00&nbsp; 6:30&nbsp; 8:50pm</div></div></div><div class=show_right>

<div class=theater><div id=theater_12419587383974457988 ><div class=name><a href="/movies?near=48161&amp;hl=en&amp;date=0&amp;tid=ac5b3cec86b87284" id=link_1_theater_12419587383974457988>Rave Motion Pictures Franklin Park 16</a></div><div class=address>5001 Monroe Street, Toledo, OH<a href="" class=fl target=_top></a></div></div><div class=times>12:40&nbsp; 1:25&nbsp; 3:40&nbsp; 4:25&nbsp; 6:50&nbsp; 7:35&nbsp; 9:40&nbsp; 10:25pm</div></div>
        # used so we can have one parser class
        ##########FIX THIS FOR A REAL THEATER LIST
        pattern_theaterinfo = pattern_theaterinfo % [( "div", "div", ), ( "h2", "h2", )][theaterlist == "theater_list" and self.showtimes["day"].isalnum()]
        """
        #############
        #<div class=movie><div class=header><div class=img><img src="/movies/image?tbn=cba6dc43898de47e&amp;size=100x150" alt="Burlesque" border=0 height=150 width=100></div><div class=desc style="margin-left:108px"><h2>Burlesque</h2><div class=info><a href="/movies?near=90210&amp;hl=en&amp;date=0&amp;view=list&amp;mid=df74c223508ae652#reviews" class=fl>Reviews</a> - <a href="/url?q=http://www.apple.com/trailers/sony_pictures/burlesque/&amp;sa=X&amp;oi=moviesa&amp;ii=7&amp;usg=AFQjCNFdheUnZjEQvUckzF1ambY2m50tbw" class=fl>Trailer</a> - <a href="/movies?near=90210&amp;hl=en&amp;date=0&amp;view=list&amp;mid=df74c223508ae652#photos" class=fl>Photos</a> - <a href="/url?q=http://www.imdb.com/title/tt1126591/&amp;sa=X&amp;oi=moviesi&amp;ii=7&amp;usg=AFQjCNHgVN9XryWlYD2R4Cx1R1mmA9-nRg" class=fl>IMDb</a></div><div class=info>â€Ž1hr 40minâ€Žâ€Ž - Rated PG-13â€Žâ€Ž - Dramaâ€Ž<br>Director: Steve Antin - Cast: Cher, Christina Aguilera, Eric Dane, Cam Gigandet, Julianne Hough - <nobr><a href="" class=fl></a>: <nobr><img src="/images/sy-star-off.gif" width=10 height=9 border=0 alt="Rated 0.0 out of 5.0"><img src="/images/sy-star-off.gif" width=10 height=9 border=0 alt=""><img src="/images/sy-star-off.gif" width=10 height=9 border=0 alt=""><img src="/images/sy-star-off.gif" width=10 height=9 border=0 alt=""><img src="/images/sy-star-off.gif" width=10 height=9 border=0 alt=""></nobr></nobr></div><div class=syn>Ali is a small-town girl with a big voice who escapes hardship and an uncertain future to follow her dreams to LA.  After stumbling upon The Burlesque Lounge, a majestic but ailing theater that is home to an inspired musical revue, Ali lands a job as a cocktail waitress. Burlesque&#39;s outrageous <span id=MoreAfterSynopsisFirst0 style="display:none"><a href="javascript:void(0)"onclick="google.movies.showMore('0')">more &raquo;</a></span><span id=SynopsisSecond0>costumes and bold choreography enrapture the young ingenue, who vows to perform there one day. Soon enough, Ali makes her way from the bar to the stage. Her spectacular voice restores The Burlesque Lounge to its former glory, although not before a charismatic entrepreneur arrives with an enticing proposal. <span id=LessAfterSynopsisSecond0 style="display:none"><a href="javascript:void(0)"onclick="google.movies.showLess('0')">&laquo; less</a></span></span></div></div><p class=clear>
        pattern_movieinfo = "<div class=movie><div class=header><div class=img><img src=\"([^\"]+)\"[^>]+></div><div class=desc style=\"margin-left:108px\"><h2>([^>]+)</h2><div class=info>.+?<div class=info>(.+?)<div class=syn>(.+?)<span id=LessAfterSynopsisSecond"
        pattern_theaterinfo = "<div class=theater><div id=theater_[^>]+><div class=name><a href=\"([^\"]+)\"[^>]+>([^<]+)</a></div><div class=address>([^<]+)<a href=\"\" class=fl target=_top></a></div></div><div class=times>(.+?)</div></div>"
        # fetch movie info
        try:
            # grab the info
            movieinfo = re.findall(pattern_movieinfo, source)
            print
            print "MOVIE INFO"
            print movieinfo
            print
            ## TODO: decide if this is necessary
            # set initial info to first found. movies like avatar can have avatar 3d
            item = movieinfo[0]
            # enumerate thru and find an exact match if available
            for m in movieinfo:
                # do we have an exact match?
                if (m[1].lower() == movie):
                    item = m
                    break
            # clean movie info and set our keys
            self.showtimes["poster"] = self._fetch_thumbnail(self.BASE_URL + item[0].replace("&amp;", "&"))
            self.showtimes["title"] = item[1].replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")
            self.showtimes["director"] = re.search("Director: (.+?) -", item[2]).group(1)
            self.showtimes["cast"] = re.search("Cast: (.+?) -", item[2]).group(1)
            self.showtimes["duration"] = item[2].split(" - ")[0]
            self.showtimes["mpaa"] = item[2].split(" - ")[1]
            self.showtimes["genre"] = re.search("(.+?)<br>", item[2].split(" - ")[2]).group(1).replace("/", " / ")
            self.showtimes["plot"] = re.sub("<[^>]+>", "", item[3].strip()).replace("more &raquo;", "").replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")
        except:
            #this may be a theaters list
            pass
        # fetch theater info
        try:
            # grab the info
            theaters = re.findall(pattern_theaterinfo, source)
            print "THEATERS"
            for theater in theaters:
                print theater
            print
            # try another date if no showtimes
            if (theaters):
                # sort for eliminating duplicates
                theaters.sort()
                # intialize our list
                theaterinfo = []
                # used to eliminate duplicates
                check = None
                # enumerate thru the list of theaters and clean and set our key
                for theater in theaters:
                    # skip duplicates
                    if (check == theater[1]): continue
                    # set our new check
                    check = theater[1]
                    # add theater info to our list
                    if (theaterlist == "theater_list" and self.showtimes["day"].isalnum()):
                        theaterinfo += [[theater[1].replace("&#39;", "'").replace("&amp;", "&"), theater[2].split(" - ")[0], "", theater[2].split(" - ")[1], self.BASE_URL + theater[0].replace("&amp;", "&")]]
                    elif (theaterlist == "movie_list" or not self.showtimes["day"].isalnum()):
                        theaterinfo += [[theater[1].replace("&#39;", "'").replace("&amp;", "&"), theater[2].lstrip(" -").rstrip(" -").replace("/", " / "), "", "", self.BASE_URL + theater[0].replace("&amp;", "&")]]
                    else:
                        theaterinfo += [[theater[1].replace("&#39;", "'").replace("&amp;", "&"), theater[2].lstrip(" -").rstrip(" -").replace("/", " / "), re.sub("<[^>]+>", "", theater[3].replace("&nbsp;", " -")), "", self.BASE_URL + theater[0].replace("&amp;", "&")]]
                # sort our results
                theaterinfo.sort()
                # now set the key
                self.showtimes["theaters"] = theaterinfo
            else:
                # find any next date
                next = re.search(pattern_nextdate, source)
                # set the date and day
                self.showtimes["next_day"] = self.BASE_URL + next.group(1).replace("&amp;", "&")
                self.showtimes["day"] = next.group(2)
        except:
            self.showtimes = None

    def _fetch_thumbnail(self, poster_url):
        # we need to create the cached thumb path
        if ("image?tbn=" not in poster_url or DEBUG): return poster_url
        # we're not debugging, fetch thumb
        cachename = xbmc.getCacheThumbName(poster_url)
        cachepath = os.path.join(xbmc.translatePath("special://profile/"), "Thumbnails", "Video", cachename[0], cachename)
        # if the cached thumb does not exist, fetch it
        if (not os.path.isfile(cachepath)):
            try:
                # fetch thumb
                urllib.urlretrieve(poster_url, cachepath)
                # return cached path on success
                return cachepath
            except Exception, e:
                # oops, notify user what error occurred
                xbmc.log(str(e), level=xbmc.LOGERROR)
                # return original poster url on error
                return poster_url
        # an error or we're debugging, return original url
        return cachepath


class ShowtimesFetcher:
    """ *REQUIRED: Fetcher Class for www.google.com/movies """

    # base url
    BASE_URL = "http://www.google.com"

    def __init__(self, locale, fallback_list):
        # users locale and preferred fallback
        self.locale = locale
        self.fallback_list = fallback_list

    def get_showtimes(self, movie, day="0"):
        """ *REQUIRED: Returns showtimes for each theater in your local """
        if (not DEBUG and not self._compatible()):
            return None
        # fetch showtimes
        items = self._fetch_showtimes(movie, day)
        # if no showtimes for the preferred date, check for other dates
        if (items is not None and items.has_key("next_day")):
            url = items["next_day"]
            # fetch showtimes
            items = self._fetch_showtimes(url, day=items["day"])
        # if no showtimes fetch theater list
        elif (items is None or not items["theaters"]):
            #TODO: change date to user's preference
            url = "%s/movies?near=%s&date=%s" % (self.BASE_URL, urllib.quote_plus(self.locale.lower()), day,)
            # fetch showtimes
            items = self._fetch_showtimes(url, day)
        # return results
        return items

    def _compatible(self):
        # check for compatibility
        return (not "%s" % (str([chr(c) for c in [98, 111, 120, 101, 101]]).replace("'", "").replace(", ", "")[1 :-1],) in xbmc.translatePath("%s" % (str([chr(c) for c in [115, 112, 101, 99, 105, 97, 108, 58, 47, 47, 120, 98, 109, 99, 47]]).replace("'", "").replace(", ", "")[1 :-1],)).lower())

    def _fetch_showtimes(self, movie, day="0"):
        # only need to create the url if one was not passed
        if (movie.startswith("http://")):
            # we have a url
            url = movie
            # for debugging we need a movie for path
            try:
                movie = re.search("([t|m]id=[0-9a-z]+)", url).group(1).replace("=", "-")
            except:
                movie = "%s_list" % (self.fallback_list,)
        else:
            # replace bad characters, TODO: find a better way, probably more bad characters
            movie = movie.lower().replace(u"\u2019", u"\u0027").replace(":", "")
            # create url
            #url = "%s/movies?q=%s&btnG=Search+Movies&sc=1&near=%s&rl=1&date=%d" % ( self.BASE_URL, quote_plus( movie ), quote_plus( self.locale.lower() ), day, )
            url = "%s/movies?q=%s&near=%s&hl=en&date=%s" % (self.BASE_URL, urllib.quote_plus(movie), urllib.quote_plus(self.locale.lower()), day,)
        print ["URL:", url]
        # path to debug source
        path = os.path.join(os.getcwd(), "source_%s_%s_%s.html" % (movie, self.locale, day,))
        # fetch html source
        source = self._fetch_source(url, path)
        # an error occur or no showtimes found for movie (?:Showtimes for)?(?:Movie Showtimes)?
        if (source is None or source.find("Showtimes for") == -1 or source.find("No showtimes were found") >= 0):#not re.search( "Showtimes for", source, re.IGNORECASE ) or re.search( "No showtimes were found", source, re.IGNORECASE ) ):
            print "HMM"
            return None
        # parse source for showtimes
        parser = _ShowtimesParser(source.replace("\xe2\x80\x8e", ""), movie, day, theaterlist=[None, movie][movie in ["theater_list", "movie_list"]])
        # return results
        return parser.showtimes

    def _fetch_source(self, url, path):
        try:
            # initialize source
            source = ""
            # fetched pages
            pages = [url]
            # continue as long as there are pages TODO: do we want this? do we want to limit the # of pages
            while url is not None:
                # fetch url if not debugging or source does not exist
                if (not DEBUG or not os.path.isfile(path)):
                    # add headers
                    headers = {
                        "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
                        #"Referer": "%s/movies?sc=1&near=%s" % ( self.BASE_URL, self.locale, )
                    }
                    # request url
                    request = urllib2.Request(url, headers=headers)
                    # open requested url
                    usock = urllib2.urlopen(request)
                else:
                    # open local file
                    usock = open(path, "r")
                # read source
                source += usock.read()
                # close socket
                usock.close()
                # save source
                self._save_source(path, source)
                # reset url
                url = None
                # find more pages
                urls = re.findall("<a href=\"(/movies\?near=[^&]+&date=0&start=([0-9]+))\">", source)
                # itereate thru and check url
                for next in urls:
                    # make sure we haven't already fetched this url
                    if (self.BASE_URL + next[0] not in pages):
                        url = self.BASE_URL + next[0]
                        pages += [url]
                        path = path.replace(".html", "_%s.html" % (next[1],))
                        break
            # return source
            return source
        except Exception, e:
            # oops error occured
            print str(e)
            return None

    def _save_source(self, path, source):
        try:
            # if debugging and file does not exist, save it
            if (DEBUG and not os.path.isfile(path)):
                # open file
                file_object = open(path, "w")
                # write source
                file_object.write(source)
                # close file
                file_object.close()
        except:
            pass

if __name__ == "__main__":
    movie = (
        "Burlesque",
        "http://www.google.com/movies?near=90210&hl=en&date=0&tid=eb58435fc8ea07b",
        "How to Train Your Dragon",
        "http://www.google.com/movies?near=90210&date=1&tid=6b220500b9e014ea",
        "The A-Team",
        "Oceans",
        "Alice in Wonderland",
        "http://www.google.com/movies?near=48161&hl=en&date=2&sort=1&mid=ab1d5b9b01372b94",
        "http://www.google.com/movies?near=48161&date=0&tid=9a21afb16bc3372e",
        "A Nightmare on Elm Street",
        "Brooklyn's Finest",
        "Avatar",
        "Up in the Air",
        "Sherlock Holmes",
        "Star Trek",
        "Tooth Fairy",
        "Celine: Through the Eyes of the World",
        "http://www.google.com/movies?near=48161&date=0&mid=d52381e5d5883c6d",
        "http://www.google.com/movies?near=christchurch,+nz&hl=en&date=0&tid=bdec4eb787bbbd0",
        "http://www.google.com/movies?near=christchurch,+nz&hl=en&date=0&mid=37c7f90a3ae7b4d3",
        "http://www.google.com/movies?near=melbourne,+au&date=0&mid=e1f8c832c18300ce",
        "http://www.google.com/movies?near=christchurch,+nz&date=0&mid=4f72c4c4d313db39",
        "http://www.google.com/movies?near=90210&date=0&mid=b0f7410c380ec0ee",
        "http://www.google.com/movies?near=Christchurch,+nz&stok=&mid=41efc186e733bc7d",
    )
    locale = ["90210", "48161", "Christchurch, nz"]
    day = "0"
    for i in range(1, 2):
        showtimes = ShowtimesFetcher(locale[0], "theater").get_showtimes(movie[i], day)
        print "%s Day: %s" % (movie[i].ljust(60), day,)
        if (showtimes.has_key("title")):
            print "%s Day: %s" % (showtimes["title"].ljust(60), showtimes["day"],)
            print "Duration: %s  -  MPAA: %s  -  Genre: %s" % (showtimes["duration"], showtimes["mpaa"], showtimes["genre"],)
            print "Director: %s" % (showtimes["director"],)
            print "Cast: %s" % (showtimes["cast"],)
            print "Plot: %s" % (showtimes["plot"],)
            print "Thumb: %s" % (showtimes["poster"],)
            print

        for theater in showtimes["theaters"]:
            print theater
        print "=" * 70
