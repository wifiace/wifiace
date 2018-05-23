from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
from configparser import ConfigParser
import subprocess as sb

from core.utils_flask import logged_in, flash_errors
from core.globals import Global
from core.utils import HostapdCli, readSectionlessConfig, getPID

clients = Blueprint( "clients", __name__)

@clients.route("/")
@logged_in
def show_clients():
    client_filters = {}

    hostapd_conf = ConfigParser()
    hostapd_conf.readfp( readSectionlessConfig("root", Global.CONFIG_DIR + "/hostapd.conf") )

    if "macaddr_acl" in hostapd_conf["root"]:
        client_filters["mode"] = hostapd_conf["root"]["macaddr_acl"]

        # listing macs in accept list
        accept_list = ConfigParser(strict=False, allow_no_value=True, delimiters=(' '))
        accept_list.readfp( readSectionlessConfig("root", Global.CONFIG_DIR + "/hostapd.accept") )
        client_filters["accept_list"] = list(accept_list["root"])

        # listing macs in deny list
        deny_list = ConfigParser(strict=False, allow_no_value=True, delimiters=(' '))
        deny_list.readfp( readSectionlessConfig("root", Global.CONFIG_DIR + "/hostapd.deny") )
        client_filters["deny_list"] = list(deny_list["root"])

    else:
        client_filters = None

    # connected client to rougeap
    connect_clients = []
    if getPID("hostapd") !=-1:
        BIN_HOSTAPDCLI = Global.EXTERNAL_TOOLS_DIR + "/hostapd-mana/hostapd/hostapd_cli"
        connect_clients = HostapdCli.listConnected( BIN_HOSTAPDCLI, "/tmp/aceweb/dnsmasq.leases" )

    return render_template("clients.html", client_filters = client_filters, connect_clients=connect_clients)

@clients.route("/change_filter_mode", methods=["GET"])
@logged_in
def change_filter_mode():
    if "mode" not in request.args:
        return jsonify(message="mode not specified."), 400

    mode = str(request.args.get("mode"))

    sb.call(["sed", "-i", "s/macaddr_acl=.*/macaddr_acl=" + mode + "/" , Global.CONFIG_DIR + "/hostapd.conf"])

    return jsonify(message="mode changed " + mode)


@clients.route("/add_to_filter", methods=["GET"])
@logged_in
def add_to_filter():
    if "mac" not in request.args:
        return jsonify(message="mac not specified."), 400

    if "file" not in request.args:
        return jsonify(message="file not specified."), 400


    mac = str(request.args.get("mac"))
    mac = mac + " " + mac
    file_name = str(request.args.get("file"))

    if file_name == "accept":
        check = sb.Popen(["grep", mac, Global.CONFIG_DIR + "/hostapd.accept"], stdout=sb.PIPE).stdout.read()
        if len(check)==0:
            with open(Global.CONFIG_DIR + "/hostapd.accept", "a") as f:
                f.write(mac + "\n")
        else:
            return jsonify(message="Already exists : " + mac), 400

    elif file_name == "deny":
        print "DENY"
        check = sb.Popen(["grep", mac, Global.CONFIG_DIR + "/hostapd.deny"], stdout=sb.PIPE).stdout.read()
        if len(check)==0:
            with open(Global.CONFIG_DIR + "/hostapd.deny", "a") as f:
                f.write(mac + "\n")
        else:
            return jsonify(message="Already exists : " + mac), 400

    else:
        return jsonify(message="invailed filed specified : " + file_name ), 400

    return jsonify(message="Added to " +file_name+ " list : " + mac)


@clients.route("/remove_from_filter", methods=["GET"])
@logged_in
def remove_from_filter():
    if "mac" not in request.args:
        return jsonify(message="mac not specified."), 400

    if "file" not in request.args:
        return jsonify(message="file not specified."), 400


    mac = str(request.args.get("mac"))
    file_name = str(request.args.get("file"))

    if file_name == "accept":
        sb.call(["sed", "-i", "s/^" + mac + ".*$//Ig", Global.CONFIG_DIR + "/hostapd.accept"])

    elif file_name == "deny":
        sb.call(["sed", "-i", "s/^" + mac + ".*$//Ig", Global.CONFIG_DIR + "/hostapd.deny"])
    else:
        return jsonify(message="invailed filed specified : " + file_name ), 400

    return jsonify(message="Removed from " +file_name+ " list : " + mac)

@clients.route("/deauthenticate_connected", methods=["GET"])
@logged_in
def deauthenticate_connected():
    BIN_HOSTAPDCLI = Global.EXTERNAL_TOOLS_DIR + "/hostapd-mana/hostapd/hostapd_cli"

    if "mac" not in request.args:
        return jsonify(message="mac not specified."), 400

    mac = str(request.args.get("mac"))

    HostapdCli.deauthConnected(BIN_HOSTAPDCLI, mac)
    if request.referrer:
        return redirect(request.referrer)
    return "deauthenticate : " + mac
