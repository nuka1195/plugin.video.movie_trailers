#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
## Functions Module: Common shared functions

import datetime
import sys
import time
import xbmc


def translatePath(path):
    """Converts special:// paths and smb:// paths so os and shutil work

    """
    # translate any special:// paths
    path = xbmc.validatePath(xbmc.translatePath(path)).decode("UTF-8")
    # if windows and smb:// convert to a proper format for sqlite3, shutil and os modules
    if (path.startswith("smb://")):
        if (sys.platform == "win32" or sys.platform == "win64"):
            path = path.replace(u"/", u"\\").replace(u"smb:", u"")

    return path

def format_date(date, pretty=True, short=True, reverse=False, modified=False, hours=0):
    try:  #FIXME: clean this up, too many hacks
        # set proper format
        #print [date, xbmc.getRegion("time")]
        format_ = [
            [["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"][short], [xbmc.getRegion("dateshort"), xbmc.getRegion("datelong")][pretty]],
            ["%Y-%m-%d %H:%M:%S", "%a, %d %b %Y %H:%M:%S GMT"]
        ][modified]
        # reverse for saving in NFO and DB
        if (reverse):
            format_.reverse()
        # format as date/time
        if (modified):
            dt = datetime.datetime(*time.strptime(date, format_[0])[ : 6]) + datetime.timedelta(hours=hours)
        # format as date
        else:
            dt = datetime.date(*time.strptime(date, format_[0])[ : 3])
        # return result
        return dt.strftime(format_[1])
    except:
        # something is wrong, return original
        return date

def format_date_new(date, abbrev=False, time=False, pretty=True, if_modified=False, hours=0):
    #def format_date(date, pretty=True, short=True, reverse=False, modified=False, hours=0):
    try:  #FIXME: clean this up, too many hacks
        # set proper format

        # Thursday, March 7, 2013   -   Thu, Mar 7, 2013
        pretty_output = [xbmc.getRegion("datelong"), xbmc.getRegion("datelong").replace("%A", "%a").replace("%B", "%b")][abbrev]

        # 03/07/2013 02:30:00 pm   -   03/07/2013
        regular_output = ["{date} {hours}".format(date=xbmc.getRegion("dateShort"), time=xbmc.getRegion("dateShort")), xbmc.getRegion("dateShort")][short]

        # Thu, 13 Mar 2013 14:30:00 GMT
        if_modified_output = "%a, %d %b %Y %H:%M:%S GMT"


        format = [
            [["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"][short], [xbmc.getRegion("dateshort"), xbmc.getRegion("datelong")][pretty]],
            ["%Y-%m-%d %H:%M:%S", "%a, %d %b %Y %H:%M:%S GMT"]
        ][modified]



        """
        ['xbmc.getRegion("dateshort")', '%m/%d/%Y']
        ['xbmc.getRegion("datelong")', '%A, %B %d, %Y']
        format = {
                "input": ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"][short],
                "output": [xbmc.getRegion("dateshort"), "%a, %d %b %Y %H:%M:%S GMT"][if_modified]
            }
            "long": {
                "input": ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"][if_modified],
                "output": [xbmc.getRegion("dateshort"), "%a, %d %b %Y %H:%M:%S GMT"][if_modified]
            }


              [xbmc.getRegion("dateshort"), xbmc.getRegion("datelong")][pretty]
            ],
            ["%Y-%m-%d %H:%M:%S", "%a, %d %b %Y %H:%M:%S GMT"]
        ][if_modified]
"""
        # reverse for saving in NFO and DB
        if (reverse):
            format.reverse()
        # format as date/time
        if (modified):
            dt = datetime.datetime(*time.strptime(date, format[0])[ : 6]) + datetime.timedelta(hours=hours)
        # format as date
        else:
            dt = datetime.date(*time.strptime(date, format[0])[ : 3])
        # return result
        #print format
        return dt.strftime(format[1])
    except Exception as error:
        #print str(error)
        # something is wrong, return original
        return date

def get_refresh(date=None, expires=7, format_="%Y-%m-%d %H:%M:%S"):
    try:
        # we need a datetime object
        date = datetime.datetime(*time.strptime(date, format_)[: 6])
        # calculate refresh based on expires
        refresh = datetime.datetime.utcnow() - datetime.timedelta(days=expires) > date
    except:
        # something went wrong (date is None), refresh source
        refresh = True

    return refresh

def today(days=0, format_="%Y-%m-%d %H:%M:%S"):
    # return the current date and time + # of days
    return (datetime.datetime.now() + datetime.timedelta(days=days)).strftime(format_)
