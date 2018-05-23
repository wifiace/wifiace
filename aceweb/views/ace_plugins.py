from flask import Blueprint, render_template, redirect, url_for, session, request, flash, redirect, jsonify
import os
import shutil
import subprocess as sb

from configparser import ConfigParser

from core.utils_flask import logged_in
from core.globals import Global
from aceweb.views import Shared

ace_plugins = Blueprint( "ace_plugins", __name__)

@ace_plugins.route("/")
@ace_plugins.route("/manage_plugins")
@logged_in
def show_plugins():

    # list installed plugins
    installed_plugins = []
    for plugin in Shared.plugin_manager.getAllPlugins():
        info = {}
        info["name"] = plugin.name
        info["version"] = plugin.version
        info["author"] = plugin.author
        info["description"] = plugin.description

        installed_plugins.append(info)

    # list download plugins
    download_plugins = []
    if os.path.exists("/tmp/aceweb/source.list"):
        source_list = ConfigParser()
        source_list.read("/tmp/aceweb/source.list")

        for plugin_name in source_list.sections():
            if not Shared.plugin_manager.getPluginByName(plugin_name):
                info = {}
                info['name'] = plugin_name
                info['version'] = source_list[plugin_name]['version']
                info['author'] = source_list[plugin_name]['author']
                info['description'] = source_list[plugin_name]['description']

                download_plugins.append(info)

    return render_template("manage_plugins.html", installed_plugins=installed_plugins, download_plugins=download_plugins)

@ace_plugins.route("/manage_plugins/update_source_list")
@logged_in
def update_source_list():
    # update the source list.
    sb.call(["wget", "https://raw.githubusercontent.com/wifiace/wifiace-plugins/master/source.list", "-O", "/tmp/aceweb/source.list"])
    return jsonify(message="Update source list successfully")

@ace_plugins.route("/manage_plugins/remove/<plugin_name>")
@logged_in
def remove_plugin(plugin_name):
    plugin = Shared.plugin_manager.getPluginByName( plugin_name )
    if plugin == None:
        return jsonify(message="Plugin named : " + plugin_name + " not founded."), 400

    shutil.rmtree(os.path.dirname(plugin.path))

    return jsonify(message="Plugin named : " + plugin_name + " remove successfully.")

@ace_plugins.route("/manage_plugins/install/<plugin_name>")
@logged_in
def install_plugin(plugin_name):
    url = "https://github.com/wifiace/wifiace-plugins" + "/trunk/" + plugin_name
    op_dir = Global.PLUGINS_DIR + "/" + plugin_name + "/"

    try:
        sb.check_call(["svn", "export", url, op_dir])
    except sb.CalledProcessError:
        return jsonify(message="Plugin named : " + plugin_name + " not able to install."), 400

    return jsonify(message="Plugin named : " + plugin_name + " installed successfully.")
