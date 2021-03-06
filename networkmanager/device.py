# -*- coding: utf-8 -*-

import dbus
#from networkmanager import NetworkManager
from dbusclient import DBusClient
from dbusclient.func import *
from util import Enum, Flags
from accesspoint import AccessPoint, Mode # for Wireless
from base import Base

class Ip4Address(object):
    def __init__(self, int32):
        self.a = int32
    def __str__(self):
        ret = []
        i32 = self.a
        for i in range(4):
            ret.append("%d" % (i32 % 256))
            i32 /= 256
        return ".".join(ret)
            
class IP4Config(Base):
    """
     Properties:    
    Addresses - aau - (read)
    Nameservers - au - (read)
    Domains - as - (read)
    Routes - aau - (read)
    """

    SERVICE = "org.freedesktop.NetworkManager"
    IFACE = "org.freedesktop.NetworkManager.IP4Config"

    def __init__(self, opath):
        super(IP4Config, self).__init__(self.SERVICE, opath, default_interface = self.IFACE)

IP4Config._add_adaptors(
    Addresses = PA(identity), #TODO
    Nameservers = PA(seq_adaptor(Ip4Address)),
#    Domains = PA(identity),
    Routes = PA(identity), #TODO
    )

class DHCP4Config(Base):
    """
     Signals:
    PropertiesChanged ( a{sv}: properties )
     Properties:   
    Options - a{sv} - (read)
    """

    SERVICE = "org.freedesktop.NetworkManager"
    IFACE = "org.freedesktop.NetworkManager.DHCP4Config"

    def __init__(self, opath):
        super(DHCP4Config, self).__init__(self.SERVICE, opath, default_interface = self.IFACE)

#DHCP4Config._add_adaptors(
#    PropertiesChanged = SA(identity),
#    Options = PA(identity),
#    )

class Device(Base):
    """networkmanager device
    
     Signals:
    StateChanged ( u: new_state, u: old_state, u: reason )
    
     Properties:
    Udi - s - (read)
    Interface - s - (read)
    Driver - s - (read)
    Capabilities - u - (read) (NM_DEVICE_CAP)
    Ip4Address - i - (read)
    State - u - (read) (NM_DEVICE_STATE)
    Ip4Config - o - (read)
    Dhcp4Config - o - (read)
    Managed - b - (read)
    DeviceType - u - (read)
    
     Enumerated types:
    NM_DEVICE_STATE
    NM_DEVICE_STATE_REASON
    
     Sets of flags:
    NM_DEVICE_CAP
    """
    class State(Enum):
        UNKNOWN = 0
        UNMANAGED = 1
        UNAVAILABLE = 2
        DISCONNECTED = 3
        PREPARE = 4
        CONFIG = 5
        NEED_AUTH = 6
        IP_CONFIG = 7
        ACTIVATED = 8
        FAILED = 9

    class StateReason(Enum):
        UNKNOWN = 0
        NONE = 1
        NOW_MANAGED = 2
        NOW_UNMANAGED = 3
        CONFIG_FAILED = 4
        CONFIG_UNAVAILABLE = 5
        CONFIG_EXPIRED = 6
        NO_SECRETS = 7
        SUPPLICANT_DISCONNECT = 8
        SUPPLICANT_CONFIG_FAILED = 9
        SUPPLICANT_FAILED = 10
        SUPPLICANT_TIMEOUT = 11
        PPP_START_FAILED = 12
        PPP_DISCONNECT = 13
        PPP_FAILED = 14
        DHCP_START_FAILED = 15
        DHCP_ERROR = 16
        DHCP_FAILED = 17
        SHARED_START_FAILED = 18
        SHARED_FAILED = 19
        AUTOIP_START_FAILED = 20
        AUTOIP_ERROR = 21
        AUTOIP_FAILED = 22
        MODEM_BUSY = 23
        MODEM_NO_DIAL_TONE = 24
        MODEM_NO_CARRIER = 25
        MODEM_DIAL_TIMEOUT = 26
        MODEM_DIAL_FAILED = 27
        MODEM_INIT_FAILED = 28
        GSM_APN_FAILED = 29
        GSM_REGISTRATION_NOT_SEARCHING = 30
        GSM_REGISTRATION_DENIED = 31
        GSM_REGISTRATION_TIMEOUT = 32
        GSM_REGISTRATION_FAILED = 33
        GSM_PIN_CHECK_FAILED = 34
        FIRMWARE_MISSING = 35
        REMOVED = 36
        SLEEPING = 37
        CONNECTION_REMOVED = 38
        USER_REQUESTED = 39
        CARRIER = 40

    class DeviceType(Enum):
        UNKNOWN = 0
        ETHERNET = 1
        WIRELESS = 2
        GSM = 3
        CDMA = 4

    class Cap(Flags):
        NONE = 0x0
        NM_SUPPORTED = 0x1
        CARRIER_DETECT = 0x2

    @classmethod
    def _settings_type(cls):
        """The matching settings["connection"]["type"]"""
        return "unknown"

    SERVICE = "org.freedesktop.NetworkManager"
    IFACE = "org.freedesktop.NetworkManager.Device"

    def __init__(self, opath):
        """Inits the base class, unlike _create"""
        super(Device, self).__init__(self.SERVICE, opath, default_interface = self.IFACE)


    _constructors = {}
    @staticmethod
    def _register_constructor(type, ctor):
#        print "REGISTERING", type, repr(type), ctor
        Device._constructors[type] = ctor

    @staticmethod
    def _create(opath):
        base = Device(opath)       # Class
        type = base["DeviceType"] # _type()
#        print "TYPE", type, repr(type)
        try:
            ctor = Device._constructors[int(type)] # TODO int is not nice
#            print "CONSTRUCTING:", ctor
            return ctor(opath)
        except KeyError, e:
#            print repr(e)
            return base

        
#    def __str__(self):
# FIXME how to override str?
#    def __repr__(self):
#        return "DEVICE " + self.object_path

Device._add_adaptors(
    StateChanged = SA(Device.State, Device.State, Device.StateReason),

    Capabilities = PA(Device.Cap),
    Ip4Address = PA(Ip4Address),
    State = PA(Device.State),
    Ip4Config = PA(IP4Config),
    Dhcp4Config = PA(DHCP4Config),
    Managed = PA(bool),
    DeviceType = PA(Device.DeviceType),
    )

# FIXME make them separate to enable plugins
class Wired(Device):
    "TODO docstring, move them to the class"

    @classmethod
    def _settings_type(cls):
        return "802-3-ethernet"

    # FIXME but also use parent iface
    IFACE = "org.freedesktop.NetworkManager.Device"
    # FIXME how to get parent adaptors?
Wired._add_adaptors(
#    PropertiesChanged = SA(identity),

#    HwAddress = PA(identity),
#    Speed = PA(identity),
    Carrier = PA(bool),
    )

Device._register_constructor(Device.DeviceType.ETHERNET, Wired)


class Wireless(Device):

    class DeviceCap(Flags):
        NONE = 0x0
        CIPHER_WEP40 = 0x1
        CIPHER_WEP104 = 0x2
        CIPHER_TKIP = 0x4
        CIPHER_CCMP = 0x8
        WPA = 0x10
        RSN = 0x20

    @classmethod
    def _settings_type(cls):
        return "802-11-wireless"

Wireless._add_adaptors(
    GetAccessPoints = MA(seq_adaptor(AccessPoint)),

#    PropertiesChanged = SA(identity),
    AccessPointAdded = SA(AccessPoint),
    AccessPointRemoved = SA(AccessPoint),

    Mode = PA(Mode),
    ActiveAccessPoint = PA(AccessPoint),
    WirelessCapabilities = PA(Wireless.DeviceCap),
    )

Device._register_constructor(Device.DeviceType.WIRELESS, Wireless)
