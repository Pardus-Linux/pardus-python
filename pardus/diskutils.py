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

import binascii
import struct
import os
import glob

class EDD:
    def __init__(self):
        self.edd_dir = "/sys/firmware/edd"
        self.edd_offset = 440
        self.edd_len = 4

    def blockDevices(self):
        devices = []
        for dev_type in ["hd*", "sd*"]:
            sysfs_devs = glob.glob("/sys/block/" + dev_type)
            for sysfs_dev in sysfs_devs:
                devices.append("/dev/" + os.path.basename(sysfs_dev))
        devices.sort()
        return devices

    def match_sys(self, _a):
        b = struct.unpack("2s2s2s2s", _a)
        return "0x"+b[3]+b[2]+b[1]+b[0]

    def get_edd_sig(self, _n):
        sigfile = "%s/int13_dev%s/mbr_signature" % (self.edd_dir, _n)
        if os.path.exists(sigfile):
            sig = file(sigfile).read().strip("\n")
        else:
            sig = "NOT FOUND"

        return sig

    def get_mbr_sig(self, _f):
        f = file(_f)
        f.seek(self.edd_offset)
        a = f.read(self.edd_len)
        f.close()

        sig = self.match_sys(binascii.b2a_hex(a))
        return sig

    def list_edd_signatures(self):
        sigs = {}
        if os.path.exists(self.edd_dir):
            for d in os.listdir(self.edd_dir):
                bios_num = d[9:]
                sigs[bios_num] = self.get_edd_sig(bios_num)
        else:
            print "please insert edd module"
        return sigs

    def list_mbr_signatures(self):
        sigs = {}
        for d in self.blockDevices():
            try:
                sigs[self.get_mbr_sig(d)] = d
            except IOError:
                pass
        return sigs
