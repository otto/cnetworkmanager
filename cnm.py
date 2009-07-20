#!/usr/bin/python
VERSION = "0.20"

import sys
import dbus
from networkmanager.networkmanager import NetworkManager, SYSTEM_SERVICE, USER_SERVICE
from networkmanager.settings.settings import NetworkManagerSettings

# must be set before we ask for signals
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
# for calling quit
import gobject
loop = gobject.MainLoop()
LOOP = False

from optparse import OptionParser

op = OptionParser(version="%prog " + VERSION)

# TODO http://docs.python.org/lib/optparse-adding-new-types.html
op.add_option("-w", "--wifi",
              choices=["0","1","off","on","no","yes","false","true"],
              metavar="BOOL",
              help="Enable or disable wireless")
op.add_option("-o", "--online",
              choices=["0","1","off","on","no","yes","false","true"],
              metavar="BOOL",
              help="Enable or disable network at all")
op.add_option("--state",
              action="store_true", default=False,
              help="Print the NM state")
op.add_option("--whe", "--wireless-hardware-enabled",
              action="store_true", default=False,
              help="Print whether the WiFi is enabled")

op.add_option("-d", "--device-list", "--dev",
              action="store_true", default=False,
              help="List devices")
op.add_option("--device-info",
              help="Info about device DEV (by interface or UDI(TODO))",
              metavar="DEV")

op.add_option("--demo",
              action="store_true", default=False,
              help="Run a random demonstration of the API")
op.add_option("--activate-connection",
              help="raw API: activate the KIND(user/system) connection CON on device DEV using AP",
              metavar="[KIND],CON,DEV,[AP]")

(options, args) = op.parse_args()

nm = NetworkManager()

true_choices =  ["1", "on", "yes", "true"]
if options.wifi != None:
    nm["WirelessEnabled"] = options.wifi in true_choices
if options.online != None:
    nm.Sleep(not options.online in true_choices)
if options.state:
    print nm["State"]
if options.whe:
    print nm["WirelessHardwareEnabled"]
# style option: pretend that properties are methods (er, python properties)
# nm["WirelessEnabled"] -> nm.WirelessEnabled() (er, nm.WirelessEnabled )

if options.device_list:
    devs = nm.GetDevices()
    for dev in devs:
        print dev["Interface"], dev["DeviceType"], dev["State"]

# --device-info, TODO clean up 
def get_device(dev_spec, hint):
    candidates = []
#    print "Hint:", hint
    devs = NetworkManager().GetDevices()
    for dev in devs:
#        print dev
        if dev._settings_type() == hint:
            candidates.append(dev)
#    print "Candidates:", candidates
    if len(candidates) == 1:
        return candidates[0]
    for dev in devs:
        if dev["Interface"] == dev_spec:
            return dev
    print "Device '%s' not found" % dev_spec
    return None

def dump_prop(obj, prop_name):
    print "%s: %s" %(prop_name, obj[prop_name])

def dump_props(obj, *prop_names):
    for prop_name in prop_names:
        dump_prop(obj, prop_name)

if options.device_info != None:
    d = get_device(options.device_info, "no hint")
    if d == None:
        print "not found"
    else:
        dump_props(d, "Udi", "Interface", "Driver", "Capabilities",
               "Ip4Address", "State", "Ip4Config", "Dhcp4Config",
               "Managed", "DeviceType")
        if d._settings_type() == "802-11-wireless":
            dump_props(d, "Mode", "WirelessCapabilities")
            aap = d["ActiveAccessPoint"]
            for ap in d.GetAccessPoints():
                print " AP:", ap.object_path
                if ap.object_path == aap.object_path:
                    print "  ACTIVE"
                dump_props(ap, "Flags", "WpaFlags", "RsnFlags",
                           "Ssid", "Frequency", "HwAddress",
                           "Mode", "MaxBitrate", "Strength")
                # TODO 
#                print "Ssid(2):", ap.Get("org.freedesktop.NetworkManager.AccessPoint", "Ssid", byte_arrays=True)

        else:
            dump_prop(d, "Carrier")

#def is_opath(x):
#    return is_instance(x, str) and x[0] == "/"

# move this to networkmanagersettings
def get_connection(svc, conn_spec):
#    if is_opath(conn_spec):
#        return conn_spec
    applet = NetworkManagerSettings(svc)
    for conn in applet.ListConnections():
        cs = conn.GetSettings()
        if cs["connection"]["id"] == conn_spec:
            return conn
    print "Connection '%s' not found" % conn_spec
    return None

def get_connection_devtype(conn):
    cs = conn.GetSettings()
    return cs["connection"]["type"]

if options.activate_connection != None:
    (svc, conpath, devpath, appath) = options.activate_connection.split(',')
    if svc == "" or svc == "user":
        svc = USER_SERVICE
    elif svc == "system":
        svc = SYSTEM_SERVICE

    conn = get_connection(svc, conpath)
    hint = get_connection_devtype(conn)
    dev = get_device(devpath, hint)
    if appath == "":
        appath = "/"
#    nm.WatchState()
    # TODO make it accept both objects and opaths
    nm.ActivateConnection(svc, conn, dev, appath)
    # TODO (optionally) block only until a stable state is reached
    LOOP = True

######## demo ##########

from networkmanager.dbusclient import DBusMio
mio = DBusMio(dbus.SystemBus(), "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
i = mio.Introspect()
d = mio.GetDevices()

def print_state_changed(*args):
    print "State changed:", ",".join(map(str,args))

if options.demo:
    nm = NetworkManager()

# TODO: generic signal (adapt cnm monitor), print name and args

    nm._connect_to_signal("StateChanged", print_state_changed)

    devs = nm.GetDevices()
    print "ActiveConnections:", nm["ActiveConnections"]

    for d in devs:
        print "\n DEVICE"
        # TODO: find API for any object
        d._connect_to_signal("StateChanged", print_state_changed)
        
    LOOP = True

# TODO wrap this
if LOOP:
    try:
        print "Entering mainloop"
        loop.run()
    except KeyboardInterrupt:
        print "Loop exited"