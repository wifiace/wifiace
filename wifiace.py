#!/usr/bin/python

""" WiFiACE is handy modular tool for pentesting wireless networks. """

__author__ = "Ashish Chavan && Abhijeet Karve"
__email__  = "0theundefined@gmail.com && karveabhijeet@gmail.com"
__version__ = "1.0"
__license__= """
Copyright (c) 2018 Ashish Chavan <0theundefined@gmail.com> and Abhijeet Karve <karveabhijeet@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
USA

"""
import os
import signal
import sys
import logging
import time
import subprocess as sb
import argparse
import os
import apt
import fcntl
import psutil

from configparser import ConfigParser

from flask import jsonify, request, redirect, flash, session
from multiprocessing import Process, Queue
from werkzeug.serving import run_simple

from aceweb.launch_ace import create_app, register_plugins
from core.globals import Global
from core.utils import getPID, termKill

proc_queue = None

PROGRAM_NAME = "wifiace"
START_MSG = "Staring " + PROGRAM_NAME + "\n"
STOP_MSG = "Bye Bye."

DESCRIPTION = "This script starts flask server and deploys wifiace-web on it."
DEBUG_DESCRIPTION = "Starts wifiace in debug mode.(Warning:Instace checking doesn't work in this mode.)"
HOST_DESCRIPTION = "IP address on which the server should bind leave it blank to bind to localhost"
PORT_DESCRIPTION = "port for the webserver to run on (Default : 5000)"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def exit_gracefully(signal, stack_frame):
    print STOP_MSG
    sys.exit(0)

def check_dependency():
    DEPENDENCIES = ["aircrack-ng", "dnsmasq", "macchanger", "subversion"]

    all_ok = True

    cache = apt.cache.Cache()

    # check if the dependent packages are installed.
    all_ok = True
    for pack in DEPENDENCIES:
        if pack in cache:
            if not cache[pack].is_installed:
                print "[ERROR]Package : ", pack, " - Missing"
                all_ok = False
        else:
            print "[ERROR]Package : ", pack, " - Missing"
            all_ok = False

    # check if hostapd-mana present and builded.
    if not os.path.exists(ROOT_DIR + "/external_tools/hostapd-mana/hostapd/hostapd"):
        print "[ERROR]No binary for hostapd-mana found in 'external_tools/hostapd-mana/hostapd/'"
        all_ok = False


    # check if wifiace.conf file exists.
    if not os.path.exists(Global.WIFIACE_CONF):
        print "[ERROR]Config File : ", Global.WIFIACE_CONF, "Doesn't exist."
        all_ok = False

    if not all_ok:
        print "[INFO]run the 'setup.sh' script to automatically install the dependencies and configure wifiace."
        sys.exit(1)

def start_wifiace(queue, host, port, debug):

    # adding yapsy log handler
    yapsy_log = logging.getLogger("yapsy")
    ch = logging.StreamHandler(sys.stderr)
    # format logs .
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    yapsy_log.addHandler(ch)

    # create application.
    app = create_app()
    # register plugins
    print "---- Plugins activation messages ----"
    plugins_list = register_plugins(app)
    print "----- ---- ---- ---- ---- ----  -----"

    # inject navbar elements into the context.
    @app.context_processor
    def inject_navbar():
        return dict(navbar=plugins_list)

    # restart server.
    @app.route("/restart_server")
    def restart_server():
        if proc_queue == None:
            return jsonify(message="Failed to Restart"), 400
        proc_queue.put("restart")
        return jsonify(message="Restarted successfully")

    # shutdown server and logut users.
    @app.route("/shutdown_server")
    def shutdown_server():
        if proc_queue == None:
            return jsonify(message="Failed to shutdown"), 400

        proc_queue.put("shutdown")

        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        return jsonify(message="Server shutting down, bye bye")


    proc_queue = queue

    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == "__main__":

    # this file will act as a semafore to check our running instances.
    PID_FILE = ROOT_DIR + "/config/pidfile"

    # check if executed as root, if not sys.exit.
    if os.getuid() != 0:
        print "[WARNING]This script must be executed as root"
        sys.exit(1)

    # add clt-c signal handler
    signal.signal(signal.SIGINT, exit_gracefully)

    # check dependencies.
    check_dependency()

    # command line options
    parser = argparse.ArgumentParser( prog = PROGRAM_NAME, description = DESCRIPTION )
    parser.add_argument("-a", "--host", help = HOST_DESCRIPTION)
    parser.add_argument("-p", "--port", help = PORT_DESCRIPTION)
    parser.add_argument("-D", "--debug", help = DEBUG_DESCRIPTION, action = "store_true")

    opt = parser.parse_args()

    # open file for writing.
    pidfile = open(PID_FILE, "w")

    if opt.debug == False:
        # check if already running instance if not create an pidfile and lock it.
        # try to aquire a lock. if not able to already an instance is running
        try:
            fcntl.lockf(pidfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print "[WARNING]Another instance of ", PROGRAM_NAME, "is already running"
            sys.exit(1)

    # open wifiace.conf to get default host and port values.
    default_host = "localhost"
    default_port = 5000

    try:
        wconf = ConfigParser()
        wconf.read( Global.WIFIACE_CONF )
        default_host = wconf["core"]["host"]
        default_port = wconf["core"]["port"]
    except Exception, e:
        print "[ERROR]wifiace.conf not configured properly."
        print str(e)
        sys.exit(1)

    # default values
    if not opt.host:
        opt.host = default_host
    if not opt.port:
        opt.port = default_port

    opt.port = int(opt.port)

    # enable the restart feature only in non-debug mode (i.e debug=False) as debug=True will automatimacly have that feature.
    if opt.debug == False:
        # disabling flask console log messages.
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        print START_MSG
        print "[INFO]Starting in normal mode."
        print "[INFO]Running on http://" + opt.host + ":" + str(opt.port) + "/\n"

        q = Queue()
        proc = Process(target=start_wifiace, args=[q, opt.host, opt.port, False])

        proc.start()
        #waithing queue, if there is no call than sleep, otherwise break
        while True:
            if q.empty():
                time.sleep(1)
            else:
                break
        #terminate and then restart the app on subprocess
        proc.terminate()

        # close the file.
        pidfile.close()

        op = q.get()
        if op == "restart":
            args = [sys.executable] + [sys.argv[0]]
            sb.call(args)
        elif op == "shutdown":
            sys.exit(0)
    else:
        print "[INFO]Starting in degub mode."
        print opt.port, opt.host

        start_wifiace(None, opt.host, opt.port, True)

    # close the file.
    pidfile.close()
