#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## XBMCAddon module: Subclasses xbmcaddon.Addon

from urllib import unquote_plus
import sys
import xbmc
import xbmcaddon

__all__ = ["XBMCAddon"]


class XBMCAddon(xbmcaddon.Addon):
    """XBMCAddon Class:

    Subclass of xbmcaddon.Addon class.

    params: a dict() holding all parameters set by addon.
            including "path" and "handle"

    getSetting: method to override xbmcaddon's getSetting() method.
                returning proper values so no conversion is necessary
                elsewhere.

    setSetting: method to override xbmcaddon's setSetting() method.
                converting settings as necessary back to strings.

    params: dict() to hold all parameters set by addon, including
            sys.argv[0] -> "path" and sys.argv[1] -> "handle"

    constants: dict() to hold all addon constants

    """

    def __init__(self, *args, **kwargs):
        # initialize Addon class
        xbmcaddon.Addon.__init__(self)
        # parse sys.argv for any parameters
        self.__parse_argv()
        # set constants
        self.__set_constants()
        # set settings
        self.__set_settings()

    def __parse_argv(self):
        """parses sys.argv for any parameters and sets
           - "path" to sys.argv[0]
           - "handle" to sys.argv[1]

        """

        # path and handle are used by some modules, so set them as parameters
        self.params = {"path": sys.argv[0]}

        # media sources and scripts set sys.argv different
        if (len(sys.argv) == 3):
            argv = sys.argv[2][1:]
            self.params["handle"] = int(sys.argv[1])
        else:
            argv = sys.argv[1]
            self.params["handle"] = -1

        # we need to eval() our parameter as we repr() it before quote_plus()
        self.params.update(dict(
            [param.split("=")[0], eval(unquote_plus(param.split("=")[1]))]
            for param in argv.split("&") if (param)
        ))

    def __set_constants(self):
        # constant names used for settings limits
        self.constants = {
            "DOWNLOAD_RATE_NO_LIMIT": 1550,
        }

    def __set_settings(self):
        """sets all user preferences to proper values expected by the addon"""

        # private dict() to hold settings
        # convert settings to expected type and set
        self.__settings = {
            "startup.category": int(super(XBMCAddon, self).getSetting("startup.category")),
            "startup.category.text": super(XBMCAddon, self).getSetting("startup.category.text"),
            "source.cache.path": xbmc.translatePath(super(XBMCAddon, self).getSetting("source.cache.path").replace(
                "$PROFILE", super(XBMCAddon, self).getAddonInfo("profile")).replace(
                "$ID", super(XBMCAddon, self).getAddonInfo("id"))),
            "source.schedule.when": int(super(XBMCAddon, self).getSetting("source.schedule.when")),
            "source.last.checked": super(XBMCAddon, self).getSetting("source.last.checked"),
            "trailer.save.folder": xbmc.translatePath(super(XBMCAddon, self).getSetting("trailer.save.folder").replace(
                "$PROFILE", super(XBMCAddon, self).getAddonInfo("profile"))),
            "download.new.trailers": (super(XBMCAddon, self).getSetting("download.new.trailers") == "true" and
                                      int(super(XBMCAddon, self).getSetting("source.schedule.when")) > 0 and
                                      super(XBMCAddon, self).getSetting("trailer.save.folder") != ""),
            "download.rate.limit": int(float(super(XBMCAddon, self).getSetting("download.rate.limit"))),
            #"download.trailers.limit": (int(float(super(XBMCAddon, self).getSetting("download.trailers.limit")))),
            "trailer.scraper": super(XBMCAddon, self).getSetting("trailer.scraper"),
            "trailer.quality": ["Standard", "480p", "720p", "1080p"][int(super(XBMCAddon, self).getSetting("trailer.quality"))],
            "trailer.hd.only": (super(XBMCAddon, self).getSetting("trailer.hd.only") == "true" and
                                int(super(XBMCAddon, self).getSetting("trailer.quality")) > 1),
            "trailer.limit.mpaa": int(super(XBMCAddon, self).getSetting("trailer.limit.mpaa")),
            "trailer.nr.mpaa": int(super(XBMCAddon, self).getSetting("trailer.nr.mpaa")),
            "trailer.save.movie": (super(XBMCAddon, self).getSetting("trailer.save.movie") == "true"),
            "trailer.play.mode": [int(super(XBMCAddon, self).getSetting("trailer.play.mode")), 1][
                   self.params.has_key("download") or (super(XBMCAddon, self).getSetting("trailer.play.mode") == "2" and
                   super(XBMCAddon, self).getSetting("trailer.save.folder") == "")
                ],
            "trailer.use.title": (super(XBMCAddon, self).getSetting("trailer.use.title") == "true" and
                                  super(XBMCAddon, self).getSetting("trailer.play.mode") == "2"),
            "trailer.add.trailer": (super(XBMCAddon, self).getSetting("trailer.add.trailer") == "true"),
            "trailer.multiple": int(super(XBMCAddon, self).getSetting("trailer.multiple")),
            "search.type": int(super(XBMCAddon, self).getSetting("search.type")),
            "search.whole.words": (super(XBMCAddon, self).getSetting("search.whole.words") == "true"),
            "search.current.list": (super(XBMCAddon, self).getSetting("search.current.list") == "true"),
            "search.highlight.color": ([None, "red", "green", "blue", "yellow", "orange"][
                int(super(XBMCAddon, self).getSetting("search.highlight.color"))]),
            "fanart": [super(XBMCAddon, self).getSetting("fanart.image"),
                [None, super(XBMCAddon, self).getSetting("fanart.path")][super(XBMCAddon, self).getSetting("fanart.path") != "" and
                                                                         super(XBMCAddon, self).getSetting("fanart.type") == "0"],
                [["standard", "480p", "720p", "1080p"][int(super(XBMCAddon, self).getSetting("trailer.quality"))],
                self.params.get("category", "")][self.params.get("category", None) is not None]],
            "label2mask": ["%D", "%I", "%O", "%G", "%U"][int(super(XBMCAddon, self).getSetting("label2mask"))],
            "category1": (super(XBMCAddon, self).getSetting("category1") == "true"),
            "category2": (super(XBMCAddon, self).getSetting("category2") == "true"),
            "category3": (super(XBMCAddon, self).getSetting("category3") == "true"),
            "category4": (super(XBMCAddon, self).getSetting("category4") == "true"),
            "category5": (super(XBMCAddon, self).getSetting("category5") == "true"),
            "category6": (super(XBMCAddon, self).getSetting("category6") == "true"),
            "category7": (super(XBMCAddon, self).getSetting("category7") == "true"),
            "category8": (super(XBMCAddon, self).getSetting("category8") == "true"),
            "category9": (super(XBMCAddon, self).getSetting("category9") == "true"),
            "category10": (super(XBMCAddon, self).getSetting("category10") == "true"),
            "category11": (super(XBMCAddon, self).getSetting("category11") == "true"),
            "category12": (super(XBMCAddon, self).getSetting("category12") == "true"),
            }

    def getSetting(self, id):
        """method to override xbmcaddon.Addon().getSetting to return proper values"""

        # return converted setting in proper form
        return self.__settings.get(id, super(XBMCAddon, self).getSetting(id))

    def setSetting(self, id, value):
        """method to override xbmcaddon.Addon().setSetting to values as strings"""

        # set setting
        # FIXME: here is where we convert the value as needed before saving
        self.__settings[id] = value
        # convert to string
        if (isinstance(value, (bool, int, float))):
            value = str(value).lower()
        # save setting
        super(XBMCAddon, self).setSetting(id, value)
