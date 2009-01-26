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

"""diskutils module provides EDD class to query device boot order."""

import binascii
import fnmatch
import struct
import os
import subprocess

class EDD:
    def __init__(self):
        self.edd_dir = "/sys/firmware/edd"
        self.edd_offset = 440
        self.edd_len = 4

    def blockDevices(self):
        devices = []
        for sysfs_dev in os.listdir("/sys/block"):
            if filter(lambda x: fnmatch.fnmatch(sysfs_dev, x), ["fd*", "loop*", "ram*", "sr*"]):
                continue
            dev_name = os.path.basename(sysfs_dev)
            dev_name = dev_name.replace("!", "/")
            devices.append("/dev/" + dev_name)
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
            sig = None

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
                sig = self.get_edd_sig(bios_num)
                if sig:
                    sigs[bios_num] = sig
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

class DeviceException(Exception):
    pass

def getDeviceMap():
    subprocess.call(["/sbin/modprobe", "edd"])

    edd = EDD()
    mbr_list = edd.list_mbr_signatures()
    edd_list = edd.list_edd_signatures()

    edd_keys = edd_list.keys()
    edd_keys.sort()

    devices = []

    i = 0
    for bios_num in edd_keys:
        edd_sig = edd_list[bios_num]
        devices.append(("hd%s" % i, mbr_list[edd_sig],))
        i += 1

    return devices

def parseLinuxDevice(device):
    for grub_disk, linux_disk in getDeviceMap():
        if device.startswith(linux_disk):
            part = device.replace(linux_disk, "", 1)
            if part:
                if part.startswith("p"):
                    grub_part = int(part[1:]) - 1
                else:
                    grub_part = int(part) - 1
                return linux_disk, part, grub_disk, grub_part
    return False

def parseGrubDevice(device):
    try:
        disk, part = device.split(",")
    except ValueError:
        return False
    disk = disk[1:]
    part = part[:-1]
    if not part.isdigit():
        return False
    for grub_disk, linux_disk in getDeviceMap():
        if disk == grub_disk:
            linux_part = int(part) + 1
            if linux_disk[-1].isdigit():
                linux_part = "p%s" % linux_part
            return grub_disk, part, linux_disk, linux_part
    return False

def grubAddress(device):
    try:
        linux_disk, linux_part, grub_disk, grub_part = parseLinuxDevice(device)
    except (ValueError, TypeError):
        raise DeviceException, "No such device: %s" % device
    return "(%s,%s)" % (grub_disk, grub_part)

def linuxAddress(device):
    try:
        grub_disk, grub_part, linux_disk, linux_part = parseGrubDevice(device)
    except (ValueError, TypeError):
        raise DeviceException, "No such device: %s" % device
    return "%s%s" % (linux_disk, linux_part)
