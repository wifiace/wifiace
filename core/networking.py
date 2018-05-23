"""
This module  contains networking methods related to wireless and wired interfaces, This is
more like a wrapper module build on top of (pyric, netifaces) to make some tendious operation simple.
"""


import pyric
import netifaces
import configparser
import pyric.pyw as pyw
import subprocess as sb

# path to NetworkManager.conf
NMCONF_FILE = "/etc/NetworkManager/NetworkManager.conf"

class Wired:
    """ This class provides helpfull methods  for Wired interface. """
    # lists all wired interfaces
    @staticmethod
    def listInterfaces(prefix=""):
        """ Returns a list of all wired interfaces in the system except 'lo'.
            Arguments:
                prefix -- list only those interface which starts with the given prefix.
        """

        ifaces = netifaces.interfaces()

        result = []

        # check for wired deives with defined prefix
        for iname in ifaces:
            tmp = str(iname)
            if tmp!="lo" and pyw.iswireless(tmp)==False and tmp.startswith( prefix ):
                result.append(tmp)

        return result

    # get kernel route table
    @staticmethod
    def getRoute():
        """ Returns kernel routing table. """

        stdout = sb.Popen(["route", "-n"], stdout=sb.PIPE).stdout
        ktable = stdout.read()[:-1]
        return ktable

    # get interface status Up or Down
    @staticmethod
    def getStatus(name):
        """ Returns  string containing status of the specified interface (i.e up or down).
            Arguments:
                name -- name of the interface
        """

        stdout = sb.Popen(["cat", "/sys/class/net/"+name+"/operstate"], stdout=sb.PIPE).stdout
        status = stdout.read()[:-1]
        return status

    # get information about the interface (ip, mac, status)
    @staticmethod
    def getInfo(name):
        """ Returns  dict containing info regarding the specified interface.
            Dict : {name, ipv4, mac, status}

            Arguments:
                name -- name of the interface
        """

        addrs = netifaces.ifaddresses(name)
        mac = addrs[netifaces.AF_LINK][0]["addr"]
        try:
            ipv4 = addrs[netifaces.AF_INET][0]["addr"]
        except:
            ipv4 = None
        status = Wired.getStatus(name)

        return {"name":str(name), "ipv4":str(ipv4), "mac":str(mac) , "status":status}

    # enables the interface
    @staticmethod
    def up(name):
        """ Enables an interface """

        sb.call(["ifconfig", name, "up"])

    # disables the interface
    @staticmethod
    def down(name):
        """ Disables an interface """

        sb.call(["ifconfig", name, "down"])


# class for controlling wireless interfaces.
class Wireless:
    """ This class provides helpfull methods  for Wired interface. """

    # get Channel
    @staticmethod
    def getChannel(card_name):
        """ Returns the channel on which the card is currently
            Arguments:
                card_name -- name of the wireless card
        """

        stdout = sb.Popen(["iwlist", card_name, "channel"], stdout=sb.PIPE).stdout
        output = stdout.read()
        channel = output[-5:-3].replace(' ', '')

        # return none if channel not found
        try:
            int(channel)
        except:
            channel = -1

        return int(channel)

    # get real MacAddr
    @staticmethod
    def getRealMac(card_name):
        """ Returns the real-mac address of an interface.
            Arguments :
                card_name -- name of the wireless card
        """
        stdout = sb.Popen(["ethtool", "-P", card_name], stdout=sb.PIPE).stdout
        output = stdout.read()
        real_mac = output[output.find(':')+1 : -1]
        return real_mac

    # get info about the card
    @staticmethod
    def getInfo(card_name):
        """ Returns the dict containing info regarding the wireless card.
            Dict : {name, channel, ipv4, mac, status}

            Arguments :
                card_name -- name of the wireless card
        """
        c = pyw.getcard(card_name)
        channel = Wireless.getChannel(card_name)
        status = ""
        if pyw.isup(c):
            status = "up"
        else:
            status = "down"

        # one of this function disables during root so autload whichever available.
        ipv4 = None
        if "inetget" in dir(pyw):
            ipv4 = pyw.inetget(c)[0]
        elif "ifaddrget" in dir(pyw):
            ipv4 = pyw.ifaddrget(c)[0]

        mac = pyw.macget(c)

        return {"name":str(card_name), "channel":str(channel), "ipv4":str(ipv4), "mac":str(mac), "status":str(status)}


    # list's all wireless interfaces on the system
    @staticmethod
    def listInterfaces(mode="managed", prefix_str="", postfix_str=""):
        """ Returns the list of wireless interface.

            Arguments :
                mode -- list only those interfaces which have the given mode(default:manage)
                prefix_str -- list only those interfaces which starts with the following prefix.
                postfix_str -- list only those interfaces which ends with the following prefix.

        """
        # check if its a wireless interface
        wifaces = pyw.winterfaces()

        # list to store the result
        result = []

        # iterate through all interfaces
        for wi in wifaces:
            # create there card object
            w_card = pyw.getcard(wi)

            # check modes and prefix if specifed
            if (mode in pyw.devmodes(w_card)) and (w_card.dev.startswith( prefix_str )) and w_card.dev.endswith( postfix_str ):
                result.append(wi)

        # return a list of strings containing the names of the interfaces.
        return result

    # create's virtual interfaces
    @staticmethod
    def createVirtualInterface(old_iface, new_iface, mode="monitor", channel=1):
        """ Creates a virtual interface with the specified options and returns its pywric.Card object.
            (when creating new interface the old one is deleted.)

            Arguments :
                old_iface -- old interface name.
                new_iface -- new interface name.
                mode -- open the new interface in the given mode (default:monitor).
                channel -- start the new interface on the given channel.
        """

        # return None if invailed wireless interface
        if pyw.iswireless(old_iface)==False:
            return None

        wi = pyw.getcard(old_iface)

        # check if the specifed mode is supported by the card
        if mode in pyw.devmodes(wi):

            # create new interfaces with the specifed prefix-string default="mon"
            viface = pyw.devadd(wi, new_iface, mode)

            # delete all other interfaces with same phy id
            for card,_ in pyw.ifaces(wi):   # delete all interfaces
                if not card.dev == viface.dev:  # that are not our
                    pyw.devdel(card)

            # set default channel
            pyw.chset(viface, channel, None)

            # up the vitual interface
            pyw.up(viface)

            # return the newly created interface as pyw.Card() onject
            return viface


# class for storing and managing wireless interfaces
class WController():
    """ Class for storing and managing wireless interfaces
        here Card argument must be pywric.Card object.

    """

    def __init__(self):
        # shared monitor interface list
        self.monInterfaces = []
        # primary interface
        self.primaryMon = None
        # secondary interface
        self.secondaryMon = None
        # list to manage our locks
        self.locks = []

    # returns list of locked card
    def getLocks(self):
        """ Returns list of all locked interfaces """

        return self.locks

    # check if the given card is locked
    def isLocked(self, card):
        """ Returns True if the specifed card is locked
            Arguments :
                card -- pywric.Card Object
        """

        return card in self.getLocks()

    # locks a given card
    def lock(self, card):
        """ Locks the specifed card and returns True, else if not able to returns False.
            Arguments :
                card -- pywric.Card Object
        """

        # return if already locked.
        if self.isLocked(card):
            return False
        else:
            # else append the card to the locks list
            self.getLocks().append(card)
            return True

    # unlock the card
    def unLock(self, card):
        """ unLock the specified card and returns True, else if not able to returns False.
            Arguments :
                card -- pywric.Card Object

        """
        # return is not present is the list else remove from the lock list
        if self.isLocked(card):
            self.getLocks().remove(card)
            return True
        else:
            return False

    # set primary Monitor interface to be used
    def setPrimaryMon(self, card):
        """ Set the given 'card' as the primary Monitor interface.
            Arguments :
                card -- pywric.Card Object
        """
        self.primaryMon = card

    # set secondary Monitor Interface to be used
    def setSecondaryMon(self, card):
        """ Set the given 'card' as the secondary Monitor interface.
            Arguments :
                card -- pywric.Card Object
        """

        self.secondaryMon = card

    # get primary interface card object
    def getPrimaryMon(self):
        """ Resturns the primary Monitoring interface """

        return self.primaryMon

    # get secondary interface card object
    def getSecondaryMon(self):
        """ Resturns the secondary Monitoring interface """

        return self.secondaryMon

    # returns an valid adaptor which is not in used, priority can also be set.
    def getAdaptor(self, priorityAdaptor=None):
        """ Returns an valid adaptor which is not in used, if no available interface found returns None
            Arguments :
                priorityAdaptor -- if set it will try to get this interface 1st before tring to get other.
        """

        if priorityAdaptor == None or priorityAdaptor == self.getPrimaryMon():

            if not self.isLocked(self.getPrimaryMon()):
                return self.getPrimaryMon()
            elif not self.isLocked(self.getSecondaryMon()):
                return self.getSecondaryMon()

        elif priorityAdaptor == self.getSecondaryMon():
            if not self.isLocked(self.getSecondaryMon()):
                return self.getSecondaryMon()
            if not self.isLocked(self.getPrimaryMon()):
                return self.getPrimaryMon()

        return None

    # return an integer denoting if the card is used as what.
    def usedAs(self, card):
        """ Return an int denoting as of what the card is used as.
            Return values:
                0 -- used as PrimaryMon
                1 -- used as SecondaryMon
                2 -- none

            Arguments :
                card -- pywric.Card Object
        """

        if card == self.getPrimaryMon():
            return 0
        elif card == self.getSecondaryMon():
            return 1
        else:
            return 2

    # Returns all listed monitor interfaces
    def getMymons(self):
        """ Returns a list of added pyric.Card object in monList """
        # This list is an collection of pyw.Card() objects.
        return self.monInterfaces

    # check if the given card is already in the list
    def isMymon(self, card):
        """ Returns true if the specified 'card' is added. """
        return card in self.getMymons()

    # Add a perticular interface to the shared list
    # here input (card) should be an pyw.Card() object
    def addToMymons(self, card):
        """ Add a specified card to the list. """

        if self.isMymon(card) == False:
            self.getMymons().append(card)

            # auto set primary and secoundary mons
            if len(self.getMymons())==1 :
                self.setPrimaryMon( self.getMymons()[0] )
            elif len(self.getMymons())==2 :
                self.setSecondaryMon( self.getMymons()[1] )

            return len(self.getMymons())
        else:
            return -1

    # Removes a perticular interface from the shared list
    # here input (card) should be an pyw.Card() object
    def delFromMymons(self, card):
        """ Delete the specified card from the list. """

        if self.isMymon(card) and self.isLocked(card) == False:
            self.getMymons().remove(card)

            # auto remove primary or secondaryMon
            if self.usedAs(card) == 0 :
                self.setPrimaryMon(None)
            elif self.usedAs(card) == 1 :
                self.setSecondaryMon(None)

            return len(self.getMymons())
        else:
            return -1

    # auto loads monitor mode interfaces from the system into the shared_list
    def autoLoadMymons(self):
        """ auto loads monitor mode interfaces from the system into the list """

        wifaces = Wireless.listInterfaces(mode = "monitor", postfix_str="mon")

        myMons = self.getMymons()

        for wi in wifaces:
            card = pyw.getcard(wi)
            if card not in myMons:
                self.addToMymons(card)

        return wifaces


def listInterfaces():
    """ Return a list of all available network interfaces (except:lo)"""

    ifaces = netifaces.interfaces()
    if "lo" in ifaces:
        ifaces.remove("lo")

    return ifaces

def flushIPTable():
    """ Flushes the IPtable """

    sb.call("iptables --flush", shell=True)
    sb.call("iptables --table nat --flush", shell=True)
    sb.call("iptables --delete-chain", shell=True)
    sb.call("iptables --table nat --delete-chain", shell=True)

def enableNAT(iface1, iface2, iface2_ip):
    """ Enables NAT for the specifed interface.
        Arguments :
            iface1 -- name of the gateway iface.
            iface2 -- name of the interface on which to start NAT.
            iface2_ip  -- ip address for the iface_2 interface to be set
    """
    # eg iface1=eth0, iface2=wlan1
    sb.call(["ifconfig", iface2, iface2_ip, "up"])
    sb.call(["iptables", "--table", "nat", "--append", "POSTROUTING", "--out-interface", iface1, "-j", "MASQUERADE"])
    sb.call(["iptables", "--append", "FORWARD", "--in-interface", iface2, "-j", "ACCEPT"])
    sb.call("echo 1 > /proc/sys/net/ipv4/ip_forward", shell=True)

def setNetworkManager(ifaces_mac):
    """ Adds the given ifaces_mac to the NetworkManager.conf->unmanaged-devices list thus making it not to interfere with this interface.
        Arguments :
            ifaces_mac -- mac of the iface to be added into the unmanaged-devices.
    """

    nmConfig = configparser.ConfigParser()
    nmConfig.read(NMCONF_FILE)

    if "keyfile" not in nmConfig:
        nmConfig.add_section("keyfile")

    if "unmanaged-devices" not in nmConfig["keyfile"]:
        str_macs =";".join(["mac:" + mac for mac in ifaces_mac]) + ";"
        nmConfig["keyfile"]["unmanaged-devices"] = str_macs
    else:
        unmanaged_macs = nmConfig["keyfile"]["unmanaged-devices"].split(";")
        str_macs = ""
        for mac in ifaces_mac:
            new_mac = "mac:"+mac
            if new_mac not in unmanaged_macs:
                str_macs += new_mac+";"
        nmConfig["keyfile"]["unmanaged-devices"] = str_macs + nmConfig["keyfile"]["unmanaged-devices"]

    with open(NMCONF_FILE, "w") as configFile:
        nmConfig.write(configFile)

def resetNetworkManager():
    """ Removes the [unmanaged-devices] option from the NetworkManager.conf """

    nmConfig = configparser.ConfigParser()
    nmConfig.read(NMCONF_FILE)

    if "keyfile" in nmConfig:
        print nmConfig.remove_option("keyfile", "unmanaged-devices")

    with open(NMCONF_FILE, "w") as configFile:
        nmConfig.write(configFile)
