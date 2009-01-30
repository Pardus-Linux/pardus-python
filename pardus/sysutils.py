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

"""sysutils module provides basic system utilities."""

import os

def find_executable(exec_name):
    """find the given executable in PATH"""

    # preppend /bin, /sbin explicitly to handle system configuration
    # errors
    paths = ["/bin", "/sbin"]

    paths.extend(os.getenv("PATH").split(':'))

    for p in paths:
        exec_path = os.path.join(p, exec_name)
        if os.path.exists(exec_path):
            return exec_path

    return None

def getKernelOption(option):
    """Get a dictionary of args for the given kernel command line option"""

    try:
        cmdline = open("/proc/cmdline").read().split()
    except IOError:
        return None

    args = {}
    found = False

    for cmd in cmdline:
        if "=" in cmd:
            optName, optArgs = cmd.split("=", 1)
        else:
            optName = cmd
            optArgs = ""

        if optName == option:
            found = True

            for arg in optArgs.split(","):
                if ":" in arg:
                    k, v = arg.split(":", 1)
                    args[k] = v
                else:
                    args[arg] = ""

    return args if found else None
