import pyric.pyw as pyw
from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
import subprocess as sb

from core.utils_flask import logged_in
from core.globals import Global
from core.networking import Wired, Wireless
from core import DN

networking = Blueprint( "networking", __name__)

@networking.route("/")
@logged_in
def show_networking():
    # auto load mymons.
    Global.monCtrl.autoLoadMymons()

    kroute = Wired.getRoute()

    wirelessInfo = []
    for w in Wireless.listInterfaces():
        info = Wireless.getInfo(w)
        c = pyw.getcard(w)

        if "monitor" in pyw.devmodes(c):
            info["inUsed"] = Global.monCtrl.isMymon(c)

        info["priority"] = Global.monCtrl.usedAs(c)
        wirelessInfo.append(info)

    wiredInfo = []
    for w in Wired.listInterfaces():
        wiredInfo.append(Wired.getInfo(w))

    return render_template("networking.html", kroute=kroute, wiredInfo=wiredInfo, wirelessInfo=wirelessInfo)


# service function's provided by networking-subdomain

# enable the given interface
@networking.route("/enable_interface", methods=["GET"])
@logged_in
def enable_interface():
    if "name" not in request.args:
        return " 'name' of the interface not specified. "

    name = str(request.args.get("name"))
    Wired.up(name)
    # redirect to the source url if called from it.
    if request.referrer:
        return redirect(request.referrer)
    return  "Enabled : "+ name


# disables the given interface
@networking.route("/disable_interface", methods=["GET"])
@logged_in
def disable_interface():
    if "name" not in request.args:
        return " 'name' of the interface not specified. "

    name = str(request.args.get("name"))
    Wired.down(name)
    # redirect to the source url if called from it.
    if request.referrer:
        return redirect(request.referrer)
    return  "Disabled : "+ name


@networking.route("/create_virtual_interface", methods=["GET"])
@logged_in
def create_virtual_interface():
    if "name" not in request.args:
        return " 'name' of the interface not specified. "

    name = str(request.args.get("name"))

    card = Wireless.createVirtualInterface(name, name + "mon")
    Global.monCtrl.addToMymons(card)

    if request.referrer:
        return redirect(request.referrer)
    return  "Created : "+ card.dev

@networking.route("/revert_virtual_interface", methods=["GET"])
@logged_in
def revert_virtual_interface():
    if "name" not in request.args:
        return " 'name' of the interface not specified. "

    name = str(request.args.get("name"))
    old_card = pyw.getcard(name)

    new_name = name
    if name.find("mon") != -1:
        new_name = name[: name.find("mon")]
    new_card = Wireless.createVirtualInterface(name, new_name)
    Global.monCtrl.delFromMymons(old_card)

    if request.referrer:
        return redirect(request.referrer)
    return  "Revert To : "+ new_card.dev

@networking.route("/set_priority", methods=["GET"])
@logged_in
def set_priority():
    if ("name" not in request.args) or ("priority" not in request.args):
        return " 'name' of the interface not specified. "

    name = str(request.args.get("name"))
    pri = int(request.args.get("priority"))

    card = pyw.getcard(name)
    if pri == 0:
        Global.monCtrl.setPrimaryMon(card)
    elif pri == 1:
        Global.monCtrl.setSecondaryMon(card)

    if request.referrer:
        return redirect(request.referrer)

    return  "Priority changed for : "+ card.dev + " : to :" + str(Global.monCtrl.usedAs(card))

@networking.route("/autoload_mymons")
@logged_in
def autoload_mymons():
    Global.monCtrl.autoLoadMymons()

    if request.referrer:
        return redirect(request.referrer)
    return  "Auto-Loaded "

@networking.route("/rfkill_unblock")
@logged_in
def rfkill_unblock():
    sb.call(["rfkill", "unblock", "all"], stdout=DN, stderr=DN)
    if request.referrer:
        return redirect(request.referrer)
    return  "rfkill unblocked all interfaces."


@networking.route("/change_mac", methods=["GET"])
@logged_in
def change_mac():

    if "iface" not in request.args:
        return jsonify(message="'iface' not provided")

    if "mac" not in request.args:
        return jsonify(message="'mac' not provided")

    iface = str(request.args.get("iface"))
    mac = str(request.args.get("mac"))

    try:
        w0 = pyw.getcard(iface)
        pyw.down(w0)
        sb.check_call(["macchanger", "-m", mac, w0.dev])
        pyw.up(w0)
    except Exception, e:
        print str(e)
        return jsonify(message="Failed to change mac addr : "), 400
    return jsonify(message="Mac Address of " + iface + " is " + mac)

@networking.route("/restore_mac", methods=["GET"])
@logged_in
def restore_mac():

    if "iface" not in request.args:
        return jsonify(message="'iface' not provided")

    iface = str(request.args.get("iface"))
    mac = Wireless.getRealMac(iface).strip()
    try:
        w0 = pyw.getcard(iface)
        pyw.down(w0)
        sb.check_call(["macchanger", "-p", w0.dev])
        pyw.up(w0)
    except Exception, e:
        print str(e)
        return jsonify(message="Failed to change mac addr : "), 400
    return jsonify(message="Mac Address of " + iface + " is " + mac)

# -----------------
