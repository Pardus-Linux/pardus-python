# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

"""/etc/fstab parser facility."""

import os

def get_device_by_label(label):
    devpath = os.path.join("/dev/disk/by-label", label)
    device = None
    try:
        device = os.path.basename(os.readlink(devpath))
    except OSError:
        pass
    else:
        return os.path.join("/dev", device)

def get_device_by_uuid(uuid):
    devpath = os.path.join("/dev/disk/by-uuid", uuid)
    device = None
    try:
        device = os.path.basename(os.readlink(devpath))
    except OSError:
        pass
    else:
        return os.path.join("/dev", device)


class FstabEntry(object):
    def __init__(self, entry):
        """
        fs: First field in fstab file which determines either the device or
        special filesystems like proc, sysfs, debugfs, etc.
        mountpoint: The mountpoint to which the fs will be mounted.
        type: Filesystem type. Can be none, ignore or VFSTYPE.
        opts: Extra options to pass to the mount helper.
        dump: Defines whether the filesystem will be dumped, optional field.
        fsck: Defines whether the filesystem will be fsck'ed regularly.
        """

        fields = entry.strip().split()

        # If number of fields is < 6, either fs_freq or fs_passno is
        # not given. So we omit them and provide the defaults written in
        # fstab(5).
        self.__fs_freq = 0
        self.__fs_passno = 0

        self.__fs_spec = fields[0]
        self.__fs_file = fields[1]
        self.__fs_vfstype = fields[2]
        self.__fs_mntopts = fields[3]

        if len(fields) == 6:
            self.__fs_freq = fields[4]
            self.__fs_passno = fields[5]

        self.__volume_label = None
        self.__volume_uuid = None
        self.__device = None

        # Entry properties
        self.__is_swap = self.__fs_vfstype == "swap"
        self.__entry_ignored = self.__fs_vfstype == "ignore"
        self.__bind_move_mount = self.__fs_vfstype == "none"

        if self.__fs_spec.startswith("UUID="):
            self.__volume_uuid = self.__fs_spec.split("=")[-1]
            self.__device = get_device_by_uuid(self.__volume_uuid)

        if self.__fs_spec.startswith("LABEL="):
            self.__volume_label = self.__fs_spec.split("=")[-1]
            self.__device = get_device_by_label(self.__volume_label)

    def __str__(self):
        return """\
fs_spec: %s
fs_file: %s
fs_vfstype: %s
fs_mntopts: %s
fs_freq: %s
fs_passno: %s
""" % (self.__fs_spec,
                    self.__fs_file,
                    self.__fs_vfstype,
                    self.__fs_mntopts,
                    self.__fs_freq,
                    self.__fs_passno)

    def get_volume_label(self):
        return self.__volume_label

    def get_volume_uuid(self):
        return self.__volume_uuid

    def get_device(self):
        """Returns the device of the entry."""
        return self.__device or self.__fs_spec

    def get_mount_options(self):
        """Returns the options given in fstab in a list."""
        return self.__fs_mntopts.split(",")

    def has_mount_option(self, opt):
        """Checks whether the given option exists in fs_mntops."""
        return opt in self.get_mount_options()

    def get_file_system(self):
        """Returns the filesystem vfs type."""
        return self.__fs_vfstype

    def is_swap_entry(self):
        """Returns True if the entry corresponds to a swap area."""
        return self.__is_swap

    def is_rootfs(self):
        """Returns True if the entry corresponds to /."""
        return self.__fs_file == "/"

    def is_ignored(self):
        """Returns True if the entry should be ignored."""
        return self.__entry_ignored

    def is_mounted(self):
        """Returns True if the entry is currently mounted."""
        # Parse /proc/mounts for maximum atomicity
        for mount in open("/proc/mounts", "r").read().strip().split("\n"):
            if mount.split()[1] == self.__fs_file:
                return True
        return False


class Fstab:
    def __init__(self, _fstab="/etc/fstab"):
        """Parses fstab file given as the first parameter."""
        self.fstab = _fstab
        self.entries = []

        with open(self.fstab, "r") as fstab_entries:
            for entry in fstab_entries:
                if entry and not entry.startswith("#"):
                    self.entries.append(FstabEntry(entry))


if __name__ == "__main__":
    # Test
    fstab = Fstab()
    for entry in fstab.entries:
        print "%s %s" % (entry.get_device(), "(mounted)" if \
                entry.is_mounted() else "")
