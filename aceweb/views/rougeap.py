from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
from configparser import ConfigParser, RawConfigParser
import subprocess as sb
import os
import shutil
import time

from core.utils_flask import flash_errors, logged_in
from core.utils import *
from core.networking import *

from core.globals import Global


rougeap = Blueprint( "rougeap", __name__)

@rougeap.route('/')
@logged_in
def show_rougeap():
    HOSTAPDCLI = Global.EXTERNAL_TOOLS_DIR + "/hostapd-mana/hostapd/hostapd_cli"

    form = RougeapConfigForm()

    # READ the HOSTAPD_CONFIG configurations
    hostapd_conf = ConfigParser()
    hostapd_conf.readfp( readSectionlessConfig("root", Global.CONFIG_DIR+"/hostapd.conf") )

    # read options and assing defaults accordingly
    if "enable_mana" in hostapd_conf["root"]:
        if hostapd_conf["root"]["enable_mana"]=="1":
            form.enable_mana.process_data("checked")

    if "mana_loud" in hostapd_conf["root"]:
        if hostapd_conf["root"]["mana_loud"]=="1":
            form.mana_loud.process_data("checked")

    if "mana_macacl" in hostapd_conf["root"]:
        if hostapd_conf["root"]["mana_macacl"]=="1":
            form.mana_loud.process_data("checked")

    if "macaddr_acl" in hostapd_conf["root"]:
        form.macaddr_acl.process_data("checked")

    # read the default gateway specified.
    ifaces = Wired.listInterfaces() + Wireless.listInterfaces()

    form.gateway_interface.choices = [ (i, i) for i in ifaces ]
    with open(Global.CONFIG_DIR + "/gateway_interface", "r") as dfp:
        iface = dfp.read().strip()
        form.gateway_interface.process_data(iface)

    # check wireless_setup options
    form.wireless_setup.process_data("open")

    if "wpa" in hostapd_conf["root"]:
        if hostapd_conf["root"]["wpa"] != "0":
            form.wireless_setup.process_data("secure")

    # read SSID
    form.ssid.process_data(hostapd_conf["root"]["ssid"])

    if "wpa_passphrase" in hostapd_conf:
        # read password
        form.password.process_data(hostapd_conf["root"]["wpa_passphrase"])
    else:
        form.password.process_data("some_password")
        
    # READ DNSMASQ_CONFIG configurations

    dnsmasq_conf = RawConfigParser(strict=False, dict_type=MultiOrderedDict, allow_no_value=True)
    dnsmasq_conf.readfp( readSectionlessConfig("root", Global.CONFIG_DIR + "/dnsmasq.conf") )

    # read dhcp range
    ip_range = dnsmasq_conf.get("root", "dhcp-range").split(",")
    form.ip_start.process_data(ip_range[0])
    form.ip_end.process_data(ip_range[1])

    # read interface ip
    interface_ip = dnsmasq_conf.get("root", "dhcp-option").split("\n")
    interface_ip = interface_ip[0].split(",")[-1]
    form.interface_ip.process_data(interface_ip)


    # Deamon Status..
    deamonStatus = {}
    deamonStatus["hostapd"] = getPID("hostapd")
    if deamonStatus["hostapd"]!=-1:
        deamonStatus["hostapd-options"] = {}
        deamonStatus["hostapd-options"]["mana"] = HostapdCli.isManaEnabled(HOSTAPDCLI)
        deamonStatus["hostapd-options"]["mana-loud"] = HostapdCli.isManaLoudEnabled(HOSTAPDCLI)
        deamonStatus["hostapd-options"]["mana-macacl"] = HostapdCli.isMacAclEnabled(HOSTAPDCLI)


    deamonStatus["dnsmasq"] = getPID("dnsmasq")


    return render_template("rougeap.html", form=form, deamonStatus=deamonStatus)


@rougeap.route('/save_config', methods=["POST"])
@logged_in
def save_config():
    form = RougeapConfigForm(request.form)

    if form.validate_on_submit():
        # writing to hostapd.conf
        with open(Global.CONFIG_DIR + "/hostapd.conf", "w") as hcf:
            # mana options
            hcf.write("# mana options\n")
            if form.enable_mana.data:
                hcf.write("enable_mana=1\n")
            else:
                hcf.write("enable_mana=0\n")

            if form.enable_mana.data:
                hcf.write("mana_loud=1\n")
            else:
                hcf.write("mana_loud=0\n")

            if form.mana_macacl.data:
                hcf.write("mana_macacl=1\n")
            else:
                hcf.write("mana_macacl=0\n")

            # mac filters
            hcf.write("\n")
            if form.macaddr_acl.data:
                hcf.write("macaddr_acl=0\n")
                hcf.write("accept_mac_file="+Global.CONFIG_DIR+"/hostapd.accept\n")
                hcf.write("deny_mac_file="+Global.CONFIG_DIR+"/hostapd.deny\n")

            hcf.write("\n")
            hcf.write("interface=None\n")
            hcf.write("ssid=" + form.ssid.data+"\n")
            hcf.write("channel=1\n")

            hcf.write("\n")

            # wireless security options
            hcf.write("# wireless security options\n")
            if form.wireless_setup.data == "open":
                # open
                hcf.write("wpa=0\n")
            else:
                # secure
                hcf.write("wpa=2\n")

            hcf.write("wpa_passphrase=" + form.password.data + "\n")
            hcf.write("wpa_key_mgmt=WPA-PSK WPA-EAP\n")

            # enabling hostapd_cli
            hcf.write("\n")
            hcf.write("# enabling hostapd_cli options\n")
            hcf.write("ctrl_interface=/var/run/hostapd\n")
            hcf.write("ctrl_interface_group=0\n")

            # writing gateway interface
            with open(Global.CONFIG_DIR+"/gateway_interface", "w") as gi:
                gi.write(form.gateway_interface.data)

            # --------------------------------------------------------------
            # writing to dnsmasq.conf

            with open(Global.CONFIG_DIR + "/dnsmasq.conf", "w") as dcf:
                dcf.write("interface=None\n")

                iprange = form.ip_start.data + "," + form.ip_end.data
                dcf.write("dhcp-range=" + iprange+ "\n")

                dcf.write("dhcp-option=3," + form.interface_ip.data + "\n")
                dcf.write("dhcp-option=6," + form.interface_ip.data + "\n")

                dcf.write("server=8.8.8.8\n")
                dcf.write("no-resolv\n")
                dcf.write("domain-needed\n")
                dcf.write("log-queries\n")
                dcf.write("log-dhcp\n")
                dcf.write("dhcp-leasefile=/tmp/aceweb/dnsmasq.leases\n")
                dcf.write("log-facility=/tmp/aceweb/logs/dnsmasq.log")

    else:
        flash_errors(form)

    return redirect( url_for("rougeap.show_rougeap") )


@rougeap.route('/restore_default_config')
@logged_in
def restore_config():

    # RESTORE hostapd.conf file
    os.remove(Global.CONFIG_DIR + "/hostapd.conf")
    os.remove(Global.CONFIG_DIR + "/dnsmasq.conf")

    shutil.copy(Global.DEFAULT_CONFIG_DIR + "/hostapd.conf", Global.CONFIG_DIR + "/hostapd.conf")
    shutil.copy(Global.DEFAULT_CONFIG_DIR + "/dnsmasq.conf", Global.CONFIG_DIR + "/dnsmasq.conf")

    return redirect( url_for("rougeap.show_rougeap") )



@rougeap.route('/start_rougeap')
@logged_in
def start_rougeap():
    BIN_HOSTAPD = Global.EXTERNAL_TOOLS_DIR + "/hostapd-mana/hostapd/hostapd"

    gateway_iface = "eth0"

    dnsmasq_conf = RawConfigParser(strict=False, dict_type=MultiOrderedDict, allow_no_value=True)
    dnsmasq_conf.readfp( readSectionlessConfig("root", Global.CONFIG_DIR + "/dnsmasq.conf") )

    wlan_ifaceip = dnsmasq_conf["root"]["dhcp-option"].split(",")[-1]

    with open(Global.CONFIG_DIR + "/gateway_interface", "r") as gif:
        gateway_iface = gif.read()
        gateway_iface = gateway_iface.strip()

    # check if disconnected any adaptor.
    Global.monCtrl.autoLoadMymons()

    iface = Global.monCtrl.getPrimaryMon()

    if iface:
        try:
            Global.monCtrl.lock(iface)

            # kill process if already running
            termKill("hostapd")
            termKill("dnsmasq")

            #Config NetworkManager to not bother our device.
            setNetworkManager( Wireless.getRealMac(iface.dev) )

            # init interface in config file
            sb.call(["sed", "-i", "s/^interface=.*/interface=" + iface.dev +"/", Global.CONFIG_DIR + "/hostapd.conf", Global.CONFIG_DIR + "/dnsmasq.conf" ])

            # check for firejail
            sb.call(["dnsmasq", "-C", Global.CONFIG_DIR + "/dnsmasq.conf"])

            time.sleep(1)
            # check if dnsmasq is running
            if getPID("dnsmasq") == -1:
                flash("Failed To start DNSMASQ ( make sure your dhcp settings are configured properly.)", "warning")
                raise Exception("Dnsmasq failed to start")

            #start hostapd-mana
            sb.call("stdbuf -oL nohup " + BIN_HOSTAPD + " " + Global.CONFIG_DIR + "/hostapd.conf > " + "/tmp/aceweb/logs/hostapd.log &", shell=True)
            #sb.call(BIN_HOSTAPD + " -B " + Global.CONFIG_DIR + "/hostapd.conf", shell=True)

            time.sleep(1)
            # check if hostapd is running
            if getPID("hostapd") == -1:
                flash("Failed To start hostapd ( make sure your hostapd settings are configured properly.)", "warning")
                # stop dnsmasq
                termKill("dnsmasq")
                raise Exception("hostapd failed to start")


            # enabling internet on rougeap.
            # flushing IPTABLES
            flushIPTable()
            # Enabling NAT
            enableNAT(gateway_iface, iface.dev, wlan_ifaceip)

            flash("Started RougeAP on Interface : " + iface.dev, "success")
        except Exception, e:
            print e
            flash("Failed to start RougeAP", "warning")
            Global.monCtrl.unLock(iface)
    else:
        flash("Interface not available or busy", "warning")

    return redirect( url_for("rougeap.show_rougeap") )


@rougeap.route('/stop_rougeap')
@logged_in
def stop_rougeap():

    termKill("hostapd")
    time.sleep(1)
    termKill("dnsmasq")

    resetNetworkManager()

    iface = Global.monCtrl.getPrimaryMon()
    if Global.monCtrl.isLocked(iface):
        Global.monCtrl.unLock(iface)
        flash("Stoped RougeAp", "info")
    else:
        flash("RougeAP not running", "warning")

    return redirect( url_for("rougeap.show_rougeap") )

@rougeap.route('/change_hostapd_options', methods=["GET"])
@logged_in
def change_hostapd_options():
    BIN_HOSTAPDCLI = Global.EXTERNAL_TOOLS_DIR + "/hostapd-mana/hostapd/hostapd_cli"
    if "option" not in request.args:
        return jsonify(message="option not specified."), 400

    option = str(request.args.get("option"))

    HostapdCli.changeOptions(BIN_HOSTAPDCLI, option)
    return jsonify(message="Done : " + option)

# WTForms
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, RadioField
from wtforms.validators import IPAddress, InputRequired, Length, Regexp

class RougeapConfigForm(FlaskForm):
    enable_mana = BooleanField("Enable MANA")
    mana_loud = BooleanField("Aggressive MANA")
    mana_macacl = BooleanField("Probe MAC Filter")
    macaddr_acl = BooleanField("MAC Filter")

    gateway_interface = SelectField("Gateway Interface", choices=[("eth0", "eth0"), ("wlan0","wlan0")])

    ip_start = StringField("Start", validators=[IPAddress(ipv4=True, ipv6=False, message="Invailied Ipv4 range")])
    ip_end = StringField("End", validators=[IPAddress(ipv4=True, ipv6=False, message="Invailied Ipv4 range")])

    interface_ip = StringField("Interface Ip", validators=[IPAddress(ipv4=True, ipv6=False, message="Invailied Interface Ip")])

    wireless_setup = RadioField("Wireless Setup : ", choices=[("open", "open"), ("secure", "secure")])

    ssid = StringField("SSID", validators=[InputRequired(message="SSID Empty")])
    password = StringField("Password", validators=[Length(min=8, max=63, message="Password Length should be between 8-63 characters")])
