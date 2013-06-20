#http://www.google.com/ig/api?movies=15122

from unicodedata import normalize
from urllib import quote_plus
import StringIO
import gzip
import os
import re
import urllib2
#try:
#    import xbmc
#except:
#   pass


class Scraper:
    """ *REQUIRED: Fetcher Class for www.google.com/movies """

    # base url sort=0 theater list
    BASE_URL = "http://www.google.com/movies?near=%s&sort=%d&date=%d&time=%d&start=%d"
    """
        near = zip code or city
        sort = (0 theater list, 1 movie list)
        date = (0 today up to 15)
        time = (0 all times, 1 morning, 2 afternoon, 3 evening, 4 late)
        start =(0 increments of 10)
    """

    def __init__(self, Addon=None):
        self.Addon = Addon
        # regex's
        self.regex_movies_list = re.compile("<div class=movie><div class=header><div class=img><img src=\"([^\"]+)\"[^>]+></div><div class=desc[^>]+><h2><a href=\"([^\"]+)\">([^<]+)</a></h2><div class=info>.+?<div class=info>(.+?)<div class=syn>(.+?)<p class=clear>.+?<div class=showtimes>(.+?)<p class=clear>")
        self.regex_theater_list = re.compile("<div class=theater>.+?<a href=\"([^\"]+)\"[^>]+>([^<]+)</a></div><div class=address>([^<]+)<.+?<div class=times>([^<]+)</div></div>")

    def fetch_movies(self, _date=0, _time=0, _start=0):
        # set url
        url = self.BASE_URL % ("48161", 1, _date, _time, _start)
        # fetch and parse movies list
        movies = self._parse_html_source(self._get_html_source(url))

    def _get_html_source(self, url):
        ##############################################
        return unicode(open("movies.html", "r").read(), "UTF-8")
        # add headers
        headers = {
            "User-Agent": "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
            "Accept": "text/html; charset=UTF-8",
            "Accept-Encoding": "gzip"
        }
        # request url
        request = urllib2.Request(url, headers=headers)
        # open requested url
        usock = urllib2.urlopen(request)
        # if gzipped, we need to unzip the source,
        ## ELIMINATE CHECK AS IT's PROBABLY always zipped
        if (usock.info().getheader("Content-Encoding") == "gzip"):
            print "ZZZZZZZZZZZZZZZZZZZZIIIIIIIIIIIIIIIIIIIIIPped"
            source = gzip.GzipFile(fileobj=StringIO.StringIO(usock.read())).read()
        else:
            source = usock.read()
        # close socket
        usock.close()
        # return a unicode object
        return unicode(source, "UTF-8", "replace")

    def _parse_html_source(self, htmlSource):
        records = []
        """
            (
                u'/movies/image?tbn=212dd6ba99665f32&amp;size=100x150',
                u'/movies?near=48161&amp;sort=1&amp;date=0&amp;time=0&amp;mid=4810d65ff64f7659',
                u'Little Fockers',
                u'\u200e1hr 38min\u200e\u200e - Rated PG-13\u200e\u200e - Comedy\u200e<br>Director: Paul Weitz - Cast: Robert De Niro, Ben Stiller, Owen Wilson, Blythe Danner, Teri Polo - <nobr><a href="" class=fl></a>: <nobr><img src="/images/sy-star-off.gif" width=10 height=9 border=0 alt="Rated 0.0 out of 5.0"><img src="/images/sy-star-off.gif" width=10 height=9 border=0 alt=""><img src="/images/sy-star-off.gif" width=10 height=9 border=0 alt=""><img src="/images/sy-star-off.gif" width=10 height=9 border=0 alt=""><img src="/images/sy-star-off.gif" width=10 height=9 border=0 alt=""></nobr></nobr></div>',
                u'It has taken 10 years, two little Fockers with wife Pam and countless hurdles for Greg to finally get &quot;in&quot; with his tightly wound father-in-law, Jack.  After the cash-strapped dad takes a job moonlighting for a drug company, however, Jack&#39;s suspicions about his favorite male nurse <span id=MoreAfterSynopsisFirst0 style="display:none"><a href="javascript:void(0)"onclick="google.movies.showMore(\'0\')">more &raquo;</a></span><span id=SynopsisSecond0>come roaring back. When Greg and Pam&#39;s entire clan-including Pam&#39;s lovelorn ex, Kevin-descends for the twins&#39; birthday party, Greg must prove to the skeptical Jack that he&#39;s fully capable as the man of the house.  But, with all the misunderstandings, spying and covert missions, will Greg pass Jack&#39;s final test and become the family&#39;s next patriarch... will the circle of trust be broken for good? <span id=LessAfterSynopsisSecond0 style="display:none"><a href="javascript:void(0)"onclick="google.movies.showLess(\'0\')">&laquo; less</a></span></span></div></div>',
                u'<div class=show_left><div class=theater><div id=theater_6750433078994449928 ><div class=name><a href="/movies?near=48161&amp;sort=1&amp;date=0&amp;time=0&amp;tid=5dae5b1eb982b608" id=link_1_theater_6750433078994449928>Phoenix Theatres The Mall of Monroe</a></div><div class=address>2121 N. Monroe St., Monroe, MI<a href="" class=fl target=_top></a></div></div><div class=times>10:05am&nbsp; 12:00&nbsp; 2:10&nbsp; 4:20&nbsp; 6:35&nbsp; 8:35&nbsp; 10:35pm</div></div><div class=theater><div id=theater_11106351332624381742 ><div class=name><a href="/movies?near=48161&amp;sort=1&amp;date=0&amp;time=0&amp;tid=9a21afb16bc3372e" id=link_1_theater_11106351332624381742>Emagine Woodhaven</a></div><div class=address>21720 Allen Rd., Woodhaven, MI<a href="" class=fl target=_top></a></div></div><div class=times>3:15&nbsp; 5:30&nbsp; 7:50&nbsp; 10:10&nbsp; 11:00pm</div></div></div><div class=show_right><div class=theater><div id=theater_12419587383974457988 ><div class=name><a href="/movies?near=48161&amp;sort=1&amp;date=0&amp;time=0&amp;tid=ac5b3cec86b87284" id=link_1_theater_12419587383974457988>Rave Motion Pictures Franklin Park 16</a></div><div class=address>5001 Monroe Street, Toledo, OH<a href="" class=fl target=_top></a></div></div><div class=times>11:15am&nbsp; 12:00&nbsp; 12:45&nbsp; 1:45&nbsp; 2:30&nbsp; 3:15&nbsp; 4:15&nbsp; 5:00&nbsp; 5:45&nbsp; 6:45&nbsp; 7:30&nbsp; 8:15&nbsp; 9:15&nbsp; 10:00&nbsp; 10:45pm</div></div><div class=theater><div id=theater_13024597489691353394 ><div class=name><a href="/movies?near=48161&amp;sort=1&amp;date=0&amp;time=0&amp;tid=b4c0aa68db7f6132" id=link_1_theater_13024597489691353394>MJR Southgate Digital Cinema 20</a></div><div class=address>15651 Trenton Road, Southgate, MI<a href="" class=fl target=_top></a></div></div><div class=times>10:00&nbsp; 10:40&nbsp; 11:30am&nbsp; 12:30&nbsp; 1:00&nbsp; 2:00&nbsp; 3:00&nbsp; 4:00&nbsp; 4:45&nbsp; 5:30&nbsp; 6:30&nbsp; 7:15&nbsp; 8:00&nbsp; 9:00&nbsp; 9:40&nbsp; 10:30pm</div></div></div>')
        """
        movies = self.regex_movies_list.findall(htmlSource)
        for movie in movies:
            info = movie[ 3 ].replace(u"\u200e", "").replace(u"Rated ", "").replace(u"<br>", " - ").replace(u"Director: ", "").replace(u"Cast: ", "").split(" - ")
            plot = re.sub("<[^>]+>", "", movie[ 4 ].replace("more &raquo;", "").replace("&laquo; less", "")).strip()
            print movie[ 2 ]
            print info[ :-1 ]
            plot += "\n\n"
            theaters = self.regex_theater_list.findall(movie[ 5 ])
            for theater in theaters:
                plot += "\n".join(theater[ 1 : 4 ]).replace("&nbsp;", " ") + "\n\n"
            print
            print plot


if __name__ == "__main__":
    locale = "48161"
    scraper = Scraper()
    scraper.fetch_movies()
