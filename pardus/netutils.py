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

"""network utility functions"""

import os
import socket
import fcntl
import struct
import subprocess
import time
import pardus.csapi
from pardus.deviceutils import idsQuery

# From <bits/ioctls.h>
SIOCADDRT = 0x890B          # add routing table entry
SIOCDELRT = 0x890C          # delete routing table entry
SIOCGIFFLAGS = 0x8913       # get flags
SIOCSIFFLAGS = 0x8914       # set flags
SIOCGIFADDR = 0x8915        # get PA address
SIOCSIFADDR = 0x8916        # set PA address
SIOCGIFNETMASK = 0x891b     # get network PA mask
SIOCSIFNETMASK = 0x891c     # set network PA mask
SIOCSIFMTU = 0x8922         # set MTU size

# From <net/if.h>
IFF_UP = 0x1                # Interface is up.
IFF_BROADCAST = 0x2         # Broadcast address valid.
IFF_DEBUG = 0x4             # Turn on debugging.
IFF_LOOPBACK = 0x8          # Is a loopback net.
IFF_POINTOPOINT = 0x10      # Interface is point-to-point link.
IFF_NOTRAILERS = 0x20       # Avoid use of trailers.
IFF_RUNNING = 0x40          # Resources allocated.
IFF_NOARP = 0x80            # No address resolution protocol.
IFF_PROMISC = 0x100         # Receive all packets.
IFF_ALLMULTI = 0x200        # Receive all multicast packets.
IFF_MASTER = 0x400          # Master of a load balancer.
IFF_SLAVE = 0x800           # Slave of a load balancer.
IFF_MULTICAST = 0x1000      # Supports multicast.
IFF_PORTSEL = 0x2000        # Can set media type.
IFF_AUTOMEDIA = 0x4000      # Auto media select active.

# From <linux/if_arp.h>
ARPHRD_ETHER = 1


class IF:
    """Network interface control class"""
    def __init__(self, ifname):
        self.name = ifname
        self._sock = None
        self.timeout = "120"

        # -R -Y -N to prevent dhcpcd rewrite nameservers
        #          we should add nameservers, not rewrite them
        # -H to set hostname due to info from server
        # -t for timeout

        self.autoCmd = ["/sbin/dhcpcd", "-R", "-Y", "-N", self.name, "-t", self.timeout]

    def ioctl(self, func, args):
        if not self._sock:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return fcntl.ioctl(self._sock.fileno(), func, args)

    def _call(self, func, ip = None):
        if ip:
            ifreq = (self.name + '\0' * 16)[:16]
            data = struct.pack("16si4s10x", ifreq, socket.AF_INET, socket.inet_aton(ip))
        else:
            data = (self.name + '\0'*32)[:32]
        try:
            result = self.ioctl(func, data)
        except IOError:
            return None
        return result

    def sysValue(self, name):
        path = os.path.join("/sys/class/net", self.name, name)
        if os.path.exists(path):
            return file(path).read().rstrip("\n")
        else:
            return None

    def deviceUID(self):
        def remHex(s):
            if s.startswith("0x"):
                s = s[2:]
            return s

        modalias = self.sysValue("device/modalias")
        if not modalias:
            return "logic:%s" % self.name
        bustype, rest = modalias.split(":", 1)

        if bustype == "pci":
            vendor = remHex(self.sysValue("device/vendor"))
            device = remHex(self.sysValue("device/device"))
            return "pci:%s_%s_%s" % (vendor, device, self.name)

        if bustype == "usb":
            path = os.path.join("/sys/class/net", self.name, "device/driver")
            for item in os.listdir(path):
                if ":" in item:
                    path2 = "device/bus/devices/%s" % item.split(":", 1)[0]
                    try:
                        vendor = remHex(self.sysValue(path2 + "/idVendor"))
                        device = remHex(self.sysValue(path2 + "/idProduct"))
                    except:
                        product = "0/0/0"
                        for line in self.sysValue("device/uevent").split("\n"):
                            if line.startswith("PRODUCT="):
                                product = line.split("=")[1]
                        vendor = product.split("/")[0]
                        device = product.split("/")[1]
                    return "usb:%s_%s_%s" % (vendor, device, self.name)

        return "%s:%s" % (bustype, self.name)

    def isEthernet(self):
        nettype = self.sysValue("type")
        try:
            nettype = int(nettype)
        except (ValueError, TypeError):
            return False
        return nettype == ARPHRD_ETHER

    def isWireless(self):
        data = file("/proc/net/wireless").readlines()
        for line in data[2:]:
            name = line[:line.find(": ")].strip()
            if name == self.name:
                return True
        return False

    def isUp(self):
        result = self._call(SIOCGIFFLAGS)
        flags, = struct.unpack('H', result[16:18])
        return (flags & IFF_UP) != 0

    def up(self):
        ifreq = (self.name + '\0' * 16)[:16]
        flags = IFF_UP | IFF_RUNNING | IFF_BROADCAST | IFF_MULTICAST
        data = struct.pack("16sh", ifreq, flags)
        result = self.ioctl(SIOCSIFFLAGS, data)
        return result

    def down(self):
        ifreq = (self.name + '\0' * 16)[:16]
        result = self._call(SIOCGIFFLAGS)
        flags, = struct.unpack('H', result[16:18])
        flags &= ~IFF_UP
        data = struct.pack("16sh", ifreq, flags)
        result = self.ioctl(SIOCSIFFLAGS, data)
        return result

    def getAddress(self):
        result = self._call(SIOCGIFADDR)
        if not result:
            return None
        addr = socket.inet_ntoa(result[20:24])
        result = self._call(SIOCGIFNETMASK)
        if not result:
            return None
        mask = socket.inet_ntoa(result[20:24])
        return (addr, mask)

    def setAddress(self, address=None, mask=None):
        if address:
            result = self._call(SIOCSIFADDR, address)
            if not result:
                return False
        if mask:
            result = self._call(SIOCSIFNETMASK, mask)
            if not result:
                return False
        return True

    def getStats(self):
        tx_b = self.sysValue("statistics/tx_bytes")
        rx_b = self.sysValue("statistics/rx_bytes")
        tx_e = self.sysValue("statistics/tx_errors")
        rx_e = self.sysValue("statistics/rx_errors")
        return (tx_b, rx_b, tx_e, rx_e)

    def getSignalQuality(self):
        return self.sysValue("wireless/link")

    def getMAC(self):
        return self.sysValue("address")

    def getMTU(self):
        return self.sysValue("mtu")

    def setMTU(self, mtu):
        ifreq = (self.name + '\0' * 16)[:16]
        data = struct.pack("16si", ifreq, mtu)
        result = self.ioctl(SIOCSIFMTU, data)
        if struct.unpack("16si", result)[1] is mtu:
            return True
        return None

    def startAuto(self):
        try:
            os.unlink("/var/lib/dhcpcd/dhcpcd-%s.info" % self.name)
        except OSError:
            pass

        if self.isAuto():
            self.stopAuto()
            tt = 5
            while tt > 0 and self.isAuto():
                time.sleep(0.2)
                tt -= 0.2

        return subprocess.call(self.autoCmd)

    def stopAuto(self):
        # dhcpcd does not create a pid file until it gets 
        # an ip address so dhcpcd -k does not work while cancelling
        if subprocess.call(["/sbin/dhcpcd", "-k", self.name], stderr=file("/dev/null")):
            subprocess.call(["pkill","-f","%s" % " ".join(self.autoCmd)])

    def isAuto(self):
        path = "/var/run/dhcpcd-%s.pid" % self.name
        if not os.path.exists(path):
            return False
        pid = file(path).read().rstrip("\n")
        if not os.path.exists("/proc/%s" % pid):
            return False
        return True

    def autoInfoFile(self):
        return "/var/lib/dhcpcd/dhcpcd-" + self.name + ".info"

    def autoInfo(self):
        class AutoInfo:
            servers = None
            search = None
            gateways = None

        info_file = self.autoInfoFile()
        try:
            f = file(info_file)
        except IOError:
            return None

        info = AutoInfo()
        for line in f:
            line = line.strip()
            if line.startswith("DNS="):
                info.servers = line[4:].rstrip('\n').split(',')
            elif line.startswith("DNSSERVERS='"):
                info.servers = line[12:].rstrip('\n').rstrip("'").split(' ')
            elif line.startswith("DNSSEARCH='"):
                info.search = line[11:].rstrip('\n').rstrip("'").split(' ')
            elif line.startswith("DNSDOMAIN='"):
                info.search = line[11:].rstrip('\n').rstrip("'").split(' ')
            elif line.startswith("GATEWAYS='"):
                info.gateways = line[10:].rstrip('\n').rstrip("'").split(' ')
        return info

    def autoNameServers(self):
        info = self.autoInfo()
        if info:
            return info.servers

    def autoNameSearch(self):
        info = self.autoInfo()
        if info and info.search:
            return "".join(info.search)
        return ""

    def autoGateways(self):
        info = self.autoInfo()
        if info and info.gateways and info.gateways[0]:
            return info.gateways

def interfaces():
    """Iterate over available network interfaces"""
    for ifname in os.listdir("/sys/class/net"):
        yield IF(ifname)

def findInterface(devuid):
    """Return interface control object for given device unique id"""
    if devuid.startswith("pci:") or devuid.startswith("usb:"):
        # Simplest cast, device is in same slot
        hw, dev = devuid.rsplit("_", 1)
        ifc = IF(dev)
        if ifc.deviceUID() == devuid:
            return ifc
        # Device name is changed due to different slot/order
        for ifc in interfaces():
            ifchw = ifc.deviceUID().rsplit("_", 1)[0]
            if ifchw == hw:
                return ifc
        # Device is not inserted
        return None
    # We dont have detailed vendor/device/etc info, so just check for name
    for ifc in interfaces():
        if ifc.deviceUID() == devuid:
            return ifc
    return None

def deviceName(devuid):
    """Return product/manufacturer name for given device unique id"""
    if devuid.startswith("pci:") or devuid.startswith("usb:"):
        bustype, rest = devuid.split(":", 1)
        vendor, device, dev = rest.split("_", 2)
        if bustype == "pci":
            data = "/usr/share/misc/pci.ids"
        else:
            data = "/usr/share/misc/usb.ids"
        return idsQuery(data, vendor, device) + " (%s)" % dev
    if devuid.startswith("logic:"):
        return devuid.split(":", 1)[1]
    return devuid


class Route:
    """Network routing control class"""
    def delete(self, gw, dst = "0.0.0.0", mask = "0.0.0.0"):
        try:
            pardus.csapi.changeroute(SIOCDELRT, gw, dst, mask)
        except:
            pass

    def deleteDefault(self):
        self.delete("0.0.0.0")

    def setDefault(self, gw, dst = "0.0.0.0", mask = "0.0.0.0"):
        # We must delete previous default gateway and route entry set for gateway
        # or we will end up with multiple entries
        self.deleteDefault()
        self.delete(gw)
        try:
            pardus.csapi.changeroute(SIOCADDRT, gw, dst, mask)
        except:
            pass

def waitNet(timeout=20):
    while timeout > 0:
        upInterfaces = []
        for iface in interfaces():
            if iface.name == 'lo':
                continue
            if iface.isUp():
                try:
                    address, mask = iface.getAddress()
                except TypeError:
                    continue
                upInterfaces.append(iface)
        if len(upInterfaces):
            return True
        time.sleep(0.2)
        timeout -= 0.2
    return False
