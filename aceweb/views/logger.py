from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify, send_file
import os
from core.utils_flask import logged_in
from core.utils import getLogs
from core.globals import Global

logger = Blueprint( "logger", __name__)

@logger.route("/")
@logged_in
def show_logger():
    return render_template("logger.html")

@logger.route("/fetchlogs", methods=["GET"])
@logged_in
def fetchlogs():
    log_files = {0:"/var/log/syslog", 1:"/tmp/aceweb/logs/hostapd.log",  2:"/tmp/aceweb/logs/dnsmasq.log", }

    if "log_no" not in request.args:
        return jsonify(message="'log_no' not defined"), 400


    log_no = int(request.args.get("log_no"))

    if log_no < 0 or log_no >= len(log_files):
        return jsonify( message="Invailied log number" ), 400

    if "download" not in request.args:
        logs = getLogs( log_files[log_no], 100)
        return jsonify( message=logs )

    if os.path.exists( log_files[ log_no ] ):
        return send_file(log_files[ log_no ])
    else:
        return "Logs Not Found"
