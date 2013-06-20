#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Tasks Module: Runs common tasks

import xbmc
import xbmcgui
import xbmcvfs


class Tasks:
    """
        Tasks Class: Runs common tasks
    """

    def __init__(self, *args, **kwargs):
        # set our passed addon object
        self.m_addon = kwargs["addon"]
        print self.m_addon.params
        # do task
        exec "self.{task}()".format(task=self.m_addon.params["task"])

    def check_for_updates(self):
        def _convert_version(version):
            # split parts into major, minor & micro
            parts = version.split(".")
            # return an integer value
            return int(parts[0]) * 100000 + int(parts[1]) * 1000 + int(parts[2])
        try:
            # import needed modules
            import re
            import urllib2
            # create dialog
            pDialog = xbmcgui.DialogProgress()
            # give feedback
            pDialog.create(self.m_addon.getAddonInfo("Name"), self.m_addon.getLocalizedString(30760))
            pDialog.update(0)
            # URL to addon.xml file
            url = "{repo}{branch}{id}/addon.xml".format(repo=self.m_addon.getSetting("repo"), branch=self.m_addon.getSetting("branch"), id=self.m_addon.getAddonInfo("Id"))
            # get addon.xml source
            xml = urllib2.urlopen(url).read()
            # parse version
            version = re.search("<addon.+?version\=\"(.+?)\".*?>", xml, re.DOTALL).group(1)
        except urllib2.URLError as error:
            # set proper error messages
            msg1 = self.m_addon.getLocalizedString(30770)
            msg2 = str(error)
            msg3 = url
        else:
            # set proper message
            msg1 = self.m_addon.getLocalizedString(30700).format(version=self.m_addon.getAddonInfo("Version"))
            msg2 = ""
            msg3 = [self.m_addon.getLocalizedString(30701), self.m_addon.getLocalizedString(30702).format(version=version)][_convert_version(version) > _convert_version(self.m_addon.getAddonInfo("Version"))]

        # done, close dialog
        pDialog.close()
        # notify user of result
        ok = xbmcgui.Dialog().ok(self.m_addon.getAddonInfo("Name"), msg1, msg2, msg3)

    def configure(self):
        print "CONFIGURE"
        # open settings
        self.m_addon.openSettings()
        # TODO: edit XBMC to return a bool if settings changed and only refresh if True
        # refresh list
        xbmc.executebuiltin("Container.Refresh")

    def clean_library(self):
        import os
        # TODO: add background or foreground dialog
        # check if downloaded movies still exist, fix any missing .NFO files and missing artwork
        from database import Database
        from urllib import quote_plus
        # set database object
        self.m_database = Database(addon=self.m_addon)
        # clean library
        records = self.m_database.get_downloaded()
        # loop thru and check if trailer exists
        for record in records:
            (382,
             u'InAPPropriate Comedy',
             u'R',
             u'Freestyle Releasing',
             u'2013-03-22',
             u'\xa9 Copyright 2013 Freestyle Releasing',
             u'Vince Offer',
             u'',
             u'InAPPropriate Comedy is a no-holds barred sketch movie starring Academy Award-winner Adrien Brody as \u201cFlirty Harry,\u201d a tough, no nonsense cop with a soft middle and a flair for fashion; Rob Schneider in a dual role as both a sleazy, horny psychologist and a curmudgeonly porn critic alongside his enthusiastic counterpart Michelle Rodriguez; Lindsay Lohan living out her fantasy of taking an ultimate revenge on the salivating paparazzi who haunt her, and Ari Shaffir as \u201cThe Amazing Racist,\u201c whose hilariously offensive hidden-camera encounters with members of different ethnic and minority groups push everyone\u2019s buttons.',
             u'Rob Schneider / Michelle Rodriguez / Lindsay Lohan / Adrien Brody',
             u'Comedy',
             u'http://trailers.apple.com/trailers/independent/inappropriatecomedy/images/poster-xlarge.jpg',
             1733,
             u'Trailer 1',
             u'Standard',
             120,
             u'2013-03-18',
             21373661,
             u'http://trailers.apple.com/movies/independent/inappropriatecomedy/inappropriatecomedy-tlr1_h640w.mov',
             1,
             u'2013-03-27 12:23:41',
             u'2013-03-25 18:45:36',
             u'D:\\Trailers\\inappropriatecomedy-tlr1_h640w-trailer.mov',
             120,
             u'Trailer 1',
             u'http://trailers.apple.com/movies/independent/inappropriatecomedy/inappropriatecomedy-tlr1_h640w.mov',
             u'http://trailers.apple.com/movies/independent/inappropriatecomedy/inappropriatecomedy-tlr1_h640w.mov|2013-03-27 12:23:41',
             u'http://trailers.apple.com/movies/independent/inappropriatecomedy/inappropriatecomedy-tlr1_h640w.mov|2013-03-25 18:45:36',
             1,
             u'Apple Movie Trailers - Lite',
             u'QuickTime/7.6.2 (qtver=7.6.2;os=Windows NT 5.1Service Pack 3)', 1, u'2013-03-25 08:00:01', 7)

            #print record
            poster = record[11]
            downloaded = record[21]
            path = record[22]
            exists = xbmcvfs.exists(path.decode("UTF-8"))
            # if trailer exists, check for NFO and thumbnail
            if (exists):
                # FIXME use Export module for this
                nfo_path = u"{root}.nfo".format(root=os.path.splitext(path)[0]).decode("UTF-8")
                thumb_path = u"{root}.tbn".format(root=os.path.splitext(path)[0]).decode("UTF-8")
                if (not xbmcvfs.exists(nfo_path)):
                    print "NO NFO"
                if (not xbmcvfs.exists(thumb_path)):
                    print "{url}|User-Agent={ua}".format(url=poster, ua=quote_plus(record[30]))

                    cached_thumb = os.path.join(
                        xbmc.translatePath("special://thumbnails/"),
                        xbmc.getCacheThumbName("{url}|User-Agent={ua}".format(url=poster, ua=quote_plus(record[30])))[0],
                        xbmc.getCacheThumbName("{url}|User-Agent={ua}".format(url=poster, ua=quote_plus(record[30]))).replace(".tbn", os.path.splitext(poster)[1])
                    ).decode("UTF-8")
                    print cached_thumb, thumb_path
                    xbmcvfs.copy(cached_thumb, thumb_path)
            else:
                pass
                # update trailer
                ### FIXME:
                ###self.m_database.mark_trailer_as_downloaded(trailer=record[12], downloaded=False)
        self.m_database.commit()
        self.m_database.close()

