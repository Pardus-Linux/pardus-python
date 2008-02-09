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

"""initutils module provides ini style configuration file utils."""

import os
import ConfigParser

from pardus.fileutils import FileLock

class iniDB:
    def __init__(self, db_file, db_mode=0600):
        try:
            os.makedirs(os.path.dirname(db_file))
        except OSError:
            pass
        self.db_file = db_file
        self.lock_file = os.path.join(os.path.dirname(db_file), '.%s' % os.path.basename(db_file))
        if not os.path.exists(db_file):
            self.__writelock()
            file(db_file, "w").close()
            os.chmod(db_file, db_mode)
            self.__unlock()
        self.__readlock()
        self.cp = ConfigParser.ConfigParser()
        self.cp.read(db_file)
        self.__unlock()

    def __writelock(self):
        self.fl = FileLock(self.lock_file)
        self.fl.lock(shared=False)

    def __readlock(self):
        self.fl = FileLock(self.lock_file)
        self.fl.lock(shared=True)

    def __unlock(self):
        self.fl.unlock()

    def listDB(self):
        profiles = self.cp.sections()
        if "general" in profiles:
            profiles.remove("general")
        return profiles

    def getDB(self, name):
        dct = {}
        if name in self.cp.sections():
            dct = dict(self.cp.items(name))
        return dct

    def setDB(self, name, dct):
        for key, value in dct.iteritems():
            if value:
                if name not in self.cp.sections():
                    self.cp.add_section(name)
                self.cp.set(name, key, value)
            elif name in self.cp.sections():
                self.cp.remove_option(name, key)
        self.__writelock()
        fp = open(self.db_file, "w")
        self.cp.write(fp)
        fp.close()
        self.__unlock()

    def remDB(self, name):
        self.cp.remove_section(name)
        self.__writelock()
        fp = open(self.db_file, "w")
        self.cp.write(fp)
        fp.close()
        self.__unlock()
