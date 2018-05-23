from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from datetime import timedelta, datetime
import psutil
from urllib2 import urlopen, URLError

from core.utils_flask import logged_in
from core.utils import HostapdCli
from core.globals import Global

dashboard = Blueprint( "dashboard", __name__)

@dashboard.route("/")
@logged_in
def show_dashboard():
    info ={}

    # get uptime
    uptime_str = None
    with open("/proc/uptime") as f:
        uptime_sec = float(f.readline().split()[0])
        dt =  datetime(1, 1 ,1) + timedelta(seconds = uptime_sec)
    info["uptime"] = "%d Hours and %d Minutes" % (dt.hour, dt.minute)

    # get connected clients
    BIN_HOSTAPDCLI = Global.EXTERNAL_TOOLS_DIR + "/hostapd-mana/hostapd/hostapd_cli"
    info["connected_clients"] = len(HostapdCli.listConnected( BIN_HOSTAPDCLI, "/tmp/aceweb/dnsmasq.leases" ))

    # Cpu usage
    info["cpu_usage"] = psutil.cpu_percent(None)

    # memory usage
    info["memory_usage"] = psutil.virtual_memory().percent

    # read public ip
    info["public_ip"] = "Not connected To Internet"

    try:
        info["public_ip"] = urlopen('http://ip.42.pl/raw').read()
    except URLError, e:
        print str(e)

    return render_template("dashboard.html", info=info)
