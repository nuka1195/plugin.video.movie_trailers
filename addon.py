#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Movie Trailers: Video plugin

# enable this import for debugging
#from resources.lib import pydev_debug
from resources.lib.addonmodule import XBMCAddon

ADDON_ID = "plugin.video.movie_trailers"


if (__name__ == "__main__"):
    # we pass an instance of XBMCAddon() to all modules,
    # XBMCAddon() includes sys.argv items and parsed parameters.
    m_addon = XBMCAddon()

    # list trailers / categories
    if (m_addon.params["handle"] != -1):
        import resources.lib.trailers as trailers
        trailers.Trailers(addon=m_addon)
    # text viewer
    elif (m_addon.params.has_key("view")):
        import resources.lib.viewer as viewer
        viewer.Viewer(addon=m_addon)
    # search trailers
    elif (m_addon.params.has_key("search")):
        import resources.lib.search as search
        search.Search(addon=m_addon).search()
    # queue, download and play trailer(s)
    elif (m_addon.params.has_key("play")):
        import resources.lib.player as player
        player.Queue(addon=m_addon).queue_trailers()
    # perform tasks
    elif (m_addon.params.has_key("task")):
        import resources.lib.tasks as tasks
        tasks.Tasks(addon=m_addon)
    # movie showtimes
    elif (m_addon.params.has_key("showtimes")):
        pass
        """
        import resources.lib.showtimes as showtimes
        ui = showtimes.GUI("custom_movie.trailers-showtimes.xml", m_addon.getAddonInfo("Path"), "default", "720p", addon=m_addon)
        del ui
        """
    # screensaver
    elif (m_addon.params.has_key("screensaver")):
        import resources.lib.screensaver as screensaver
        screensaver.Screensaver(addon=m_addon)
