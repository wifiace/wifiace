from networking import WController


class Global:

    # paths.
    ROOT_DIR = ""
    CONFIG_DIR = ""
    DEFAULT_CONFIG_DIR = ""
    EXTERNAL_TOOLS_DIR = ""
    PLUGINS_DIR = ""
    WIFIACE_CONF = "/etc/wifiace.conf"

    # shared WController object
    monCtrl = WController()
