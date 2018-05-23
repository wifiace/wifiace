def register_plugins(app):

    from yapsy.PluginManager import PluginManager
    from views import ace_plugins
    from views import Shared

    Shared.plugin_manager = PluginManager(plugin_info_ext="ace-plugin")
    Shared.plugin_manager.setPluginPlaces(["plugins"])
    Shared.plugin_manager.collectPlugins()

    plugins_list = []
    # Loop round the plugins and activate/register them
    for plugin in Shared.plugin_manager.getAllPlugins():

        # check if Dependencies required by plugins are met if not install them
        if plugin.plugin_object.checkDependencies() == False:
            print plugin.name, " : Needs to install Dependencies."
            print plugin.name, " : installing Dependencies."

            plugin.plugin_object.installDependencies()

            if plugin.plugin_object.checkDependencies() == False:
                print plugin.name, " : Failed to install Dependencies."
                print plugin.name, " : Ignoring this plugin and continuing to next."
                continue

        # register the given plugin
        plugin_identifier = plugin.name.replace(" ", "")
        url_prefix = "/plugins/" + plugin_identifier
        app.register_blueprint(plugin.plugin_object.getBlueprint(), url_prefix=url_prefix)

        Shared.plugin_manager.activatePluginByName(plugin.name)

        plugins_list.append({"name":plugin_identifier, "url":url_prefix})

    return plugins_list

# initial house keepin g.
def __ini_structure(root_path):
    import os
    import shutil

    from core.globals import Global

    tmp_dir = "/tmp/aceweb"
    current_dir = root_path + "/config/"

    # check for tmp-ace direcotry if not create
    if not os.path.isdir(tmp_dir):
        os.makedirs(tmp_dir)
    # create logs folder
    if not os.path.isdir(tmp_dir + "/logs"):
        os.makedirs(tmp_dir + "/logs")
    # create config directory if doesnt exists.
    if not os.path.isdir(current_dir):
        os.makedirs(current_dir)
    # create plugin directory if doesnt exist.
    if not os.path.isdir(Global.PLUGINS_DIR):
        os.makedirs(Global.PLUGINS_DIR)

    # copy default config for hostapd/dnsmasq to current config/ folder if not present.
    if not os.path.isfile(current_dir + "/hostapd.conf"):
        shutil.copy(root_path + "/config/default/hostapd.conf", current_dir + "/hostapd.conf")

    if not os.path.isfile(current_dir + "/dnsmasq.conf"):
        shutil.copy(root_path + "/config/default/dnsmasq.conf", current_dir + "/dnsmasq.conf")

    if not os.path.isfile(current_dir + "/hostapd.accept"):
        with open(current_dir + "/hostapd.accept", 'w') as f:
            f.write("# List of MAC addresses that are allowed to authenticate (IEEE 802.11)\n")

    if not os.path.isfile(current_dir + "/hostapd.deny"):
        with open(current_dir + "/hostapd.deny", 'w') as f:
            f.write("# List of MAC addresses that are not allowed to authenticate (IEEE 802.11)\n")

    # create a file containing the default gateway interface.
    if not os.path.isfile(current_dir + "/gateway_interface"):
        with open(current_dir + "/gateway_interface", 'w') as f:
            f.write("eth0")


# Blueprint should be registered here
def __register_blueprints(app):

    from views import login, dashboard, networking, settings, recon, rougeap, clients, logger, ace_plugins

    app.register_blueprint(login.login)
    app.register_blueprint(dashboard.dashboard, url_prefix="/dashboard")
    app.register_blueprint(networking.networking, url_prefix="/networking")
    app.register_blueprint(settings.settings, url_prefix="/settings")
    app.register_blueprint(recon.recon, url_prefix="/recon")
    app.register_blueprint(rougeap.rougeap, url_prefix="/rougeap")
    app.register_blueprint(clients.clients, url_prefix="/clients")
    app.register_blueprint(logger.logger, url_prefix="/logger")
    app.register_blueprint(ace_plugins.ace_plugins, url_prefix="/plugins")



# returns root path of the app
def __init_path():
    import os, sys

    # Infer the root path from the run file in the project root (e.g. manage.py)
    fn = getattr(sys.modules['__main__'], '__file__')
    root_path = os.path.abspath(os.path.dirname(fn))

    # set the working directory path in Global
    from core.globals import Global
    Global.ROOT_DIR = root_path
    Global.CONFIG_DIR = root_path + "/config"
    Global.DEFAULT_CONFIG_DIR = root_path + "/config/default"
    Global.EXTERNAL_TOOLS_DIR = root_path + "/external_tools"
    Global.PLUGINS_DIR = root_path + "/plugins"
    return Global.ROOT_DIR


# function used to created and initialize the application.
def create_app():

    # init flask app
    from flask import Flask
    app = Flask( __name__, instance_relative_config=True)

    # loading config options
    #app.config.from_object('config')
    app.config.from_pyfile('config.py')

    # registering blueprints
    __register_blueprints(app)

    # init the working directory path to the root variable .
    app_path = __init_path()

    # init directory and folder structure for the app.
    __ini_structure( app_path )

    return app
