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
import time
import fcntl


class FileLock:
    def __init__(self, filename):
        self.filename = filename
        self.fd = None
    
    def lock(self, shared=False, timeout=-1):
        _type = fcntl.LOCK_EX
        if shared:
            _type = fcntl.LOCK_SH
        if timeout != -1:
            _type |= fcntl.LOCK_NB
        
        self.fd = os.open(self.filename, os.O_WRONLY | os.O_CREAT, 0600)
        if self.fd == -1:
            raise IOError, "Cannot create lock file"
        
        while True:
            try:
                fcntl.flock(self.fd, _type)
                return
            except IOError:
                if timeout > 0:
                    time.sleep(0.2)
                    timeout -= 0.2
                else:
                    raise
    
    def unlock(self):
        fcntl.flock(self.fd, fcntl.LOCK_UN)


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




