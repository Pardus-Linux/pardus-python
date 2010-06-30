# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

"""grubutils module provides classes for parsing grub.conf"""

import os.path

class grubCommand:
    """Grub menu command"""

    def __init__(self, key, options=[], value=""):
        self.key = key
        self.options = options
        self.value = value

    def __str__(self):
        if self.options:
            return "%s %s %s" % (self.key, " ".join(self.options), self.value)
        else:
            return "%s %s" % (self.key, self.value)

class grubEntry:
    """Grub menu entry"""

    def __init__(self, title):
        self.title = title
        self.commands = []

    def listCommands(self):
        """Returns list of commands used in entry"""
        return map(lambda x: x.key, self.commands)

    def setCommand(self, key, value, opts=[], append=False):
        """Adds a new command to entry. Optional append argument allows addition of multiple commands like 'map'."""
        if not append:
            self.unsetCommand(key)
        self.commands.append(grubCommand(key, opts, value))

    def getCommand(self, key, only_last=True):
        """Returns command object. If only_last is False, returns a list of commands named 'key'."""
        commands = filter(lambda x: x.key == key, self.commands)
        if only_last:
            try:
                return commands[-1]
            except IndexError:
                return None
        return commands

    def unsetCommand(self, key):
        """Removes 'key' from commands."""
        self.commands = filter(lambda x: x.key != key, self.commands)

    def __str__(self):
        conf = []
        conf.append("title %s" % self.title)
        for command in self.commands:
            conf.append(str(command))
        return "\n".join(conf)

class grubConf:
    """Grub configuration class."""

    def __init__(self):
        self.options = {}
        self.entries = []
        self.header = []
        self.index = 0

    def setHeader(self, header):
        """Sets grub.conf header"""
        self.header = header.split("\n")

    def __parseLine(self, line):
        """Parses single grub.conf line and returns a tupple of key, value and options."""
        line = line.replace("\t"," ")
        line = line.strip()
        try:
            key, data = line.split(" ", 1)
        except ValueError:
            key = line
            data = ""

        key = key.strip(" =")
        data = data.strip(" =")

        options = []
        values = []

        option = True
        for x in data.split():
            if option and x.startswith("--"):
                options.append(x)
            else:
                values.append(x)
                option = False

        return key, " ".join(values), options

    def parseConf(self, filename):
        """Parses a grub.conf file"""
        self.options = {}
        self.entries = []

        option = True
        entry = None

        for line in file(filename):
            if not line.strip() or line.startswith("#"):
                continue
            key, value, opts = self.__parseLine(line)

            if key == "title":
                option = False
                if entry:
                    self.entries.append(entry)
                    entry = None

            if option:
                self.options[key] = value
            else:
                if key == "title":
                    entry = grubEntry(value)
                else:
                    entry.setCommand(key, value, opts, append=True)

        if entry:
            self.entries.append(entry)

        default = os.path.join(os.path.dirname(filename), "default")
        if os.path.exists(default):
            try:
                self.index = int(file(default).read().split("\0")[0])
            except ValueError:
                self.index = 0

    def getSavedIndex(self):
        """Return last booted entry index."""
        return self.index

    def __str__(self):
        conf = []
        if self.header:
            for h in self.header:
                conf.append("# %s" % h)
            conf.append("")
        if self.options:
            for key, value in self.options.iteritems():
                line = "%s %s" % (key, value)
                conf.append(line)
            conf.append("")
        for index, entry in enumerate(self.entries):
            if entry.getCommand("savedefault"):
                entry.setCommand("savedefault", str(index))
            conf.append(str(entry))
            conf.append("")
        return "\n".join(conf)

    def write(self, filename):
        """Writes grub configuration to file."""
        file(filename, "w").write(str(self))

    def listOptions(self):
        """Returns list of options."""
        return self.options.keys()

    def setOption(self, key, value):
        """Sets an option."""
        self.options[key] = value

    def unsetOption(self, key):
        """Unsets an option."""
        del self.options[key]

    def getOption(self, key, default=""):
        """Returns value of an option."""
        return self.options.get(key, default)

    def getAllOptions(self):
        """Returns all options."""
        return ["%s %s" % (key, value) for key, value in self.options.items()]

    def listEntries(self):
        """Returns a list of entries."""
        return map(lambda x: x.title, self.entries)

    def addEntry(self, entry, index=-1):
        """Adds an entry object."""
        if index == -1:
            self.entries.append(entry)
        else:
            self.entries.insert(index, entry)

    def getEntry(self, index):
        """Returns an entry object."""
        return self.entries[index]

    def indexOf(self, entry):
        """Returns index of an entry object."""
        return self.entries.index(entry)

    def removeEntry(self, entry):
        """Removes an entry object."""
        self.entries.remove(entry)
