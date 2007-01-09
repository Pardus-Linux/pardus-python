# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

"""sysutils module provides basic file I/0 utility functions."""

import os
import codecs


class FileutilsException(Exception):
    pass


def open_utf8(filepath, mode="r"):
    """Open UTF-8 encoded file with the given mode."""

    return codecs.open(filepath, mode, "utf-8")


def save_utf8(filepath, data, overwrite=True):
    """Save UTF-8 encoded data to filepath."""

    if os.path.exists(filepath) and not overwrite:
        raise FileutilsException, "File exists: %s" % filepath

    f = codecs.open(filepath, "w", "utf-8")
    f.write(data)
    f.close()


def touch(filename):
    """Update file modification date, create file if necessary"""
    try:
        if os.path.exists(filename):
            os.utime(filename, None)
        else:
            file(filename, "w").close()
    except IOError, e:
        if e.errno != 13:
            raise
        else:
            return False
    except OSError, e:
        if e.errno != 13:
            raise
        else:
            return False
    return True




