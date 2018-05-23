from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
import thread

from core.utils_flask import logged_in,resource_lock
from core.globals import Global
from core.utils import WlanScanner, Deauth

recon = Blueprint( "recon", __name__)

@recon.route("/")
@logged_in
def show_recon():
    return render_template("recon.html")

@recon.route("/start_scan", methods=["GET"])
@logged_in
def start_scan():
    if "sec" not in request.args:
        return jsonify(message="'sec' not specified."), 400

    sec = str(request.args.get("sec"))

    iface = Global.monCtrl.getAdaptor( Global.monCtrl.getSecondaryMon())

    if iface:
        try:
            Global.monCtrl.lock(iface)
            wscan = WlanScanner("ace-var", "scan-dump")
            wscan.scan(int(sec), iface.dev)
        except:
            Global.monCtrl.unLock(iface)

        else:
            Global.monCtrl.unLock(iface)
            return jsonify(result=[ ap.toJson() for ap in wscan.parseData()])

    flash("Interface not available", 'warning')
    return jsonify(message="Interface busy or not available"), 400


@recon.route("/start_deauth", methods=["GET"])
@logged_in
def start_deauth():
    # check all required parm present .
    if not all( parm in request.args for parm in ["packets", "channel", "ap_bssid"]):
        return jsonify(message="invalid parameters passed"), 400

    # check if disconnected.
    Global.monCtrl.autoLoadMymons()
    
    iface = Global.monCtrl.getAdaptor( Global.monCtrl.getSecondaryMon())
    # if interface available.
    if iface:
        # check if client_bssid specified (meaning only disconnect this client from the AP)
        client_bssid = None
        if "client_bssid" in request.args:
            client_bssid = request.args.get("client_bssid")

        packets = int(request.args.get("packets"))
        channel = int(request.args.get("channel"))
        ap_bssid = str(request.args.get("ap_bssid"))

        thread.start_new_thread(resource_lock, (iface, Deauth.deauth, packets, channel, ap_bssid, client_bssid, iface.dev))
    else:
        return jsonify("interface busy or not available."), 403

    return jsonify(message="deauth started successfully")
