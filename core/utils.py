"""
This module  contains utilities.
"""

import re
import os
import signal
import csv
import json
import time
import StringIO
import psutil
import pyric.pyw as pyw
import subprocess as sb
from collections import OrderedDict

from core import DN

def readSectionlessConfig(section_name, file_path):
    """ Returns a StringIO with a dummy section added to it.
        this is supposed to be used with configparser.readfp() which makes the file readable by the configparser.

        Arguments :
            section_name -- dummy section name to be added .
            file_path -- path to the file to open.
    """
    fp = open(file_path)
    ini_str = "["+section_name+"]\n"+fp.read()
    dummy_fp = StringIO.StringIO(ini_str)
    fp.close()
    return dummy_fp

# remove section from config
def removeSection(section_name, file_path):
    """ Remve specified section from a file
        Arguments :
            section_name -- section name to remove from the file.
            file_path -- path to the file.
    """
    sb.call(["sed", "i", "e",  "'/["+ section_name +"]/d'", file_path ])


# for duplicate values in configparser
# source : https://stackoverflow.com/questions/15848674/how-to-configparse-a-file-keeping-multiple-values-for-identical-keys
class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super(MultiOrderedDict, self).__setitem__(key, value)


def getPID(proc_name, script=False):
    """ Returns process-id for the given running process name, if not found returns -1.
        Arguments :
            proc_name -- name of the process
            script -- when True it will search for any running script with the specified name.(default : False)
    """
    proc_pid = -1
    for proc in psutil.process_iter():
        if script:
            if proc_name in proc.cmdline():
                proc_pid = proc.pid
                break
        else:
            if proc.name() == proc_name:
                proc_pid = proc.pid
                break

    if proc_pid!=-1 and psutil.Process(proc_pid).status() != psutil.STATUS_ZOMBIE:
        return proc_pid

    return -1

def termKill(proc_name, script=False):
    """ Terminates a process with given 'proc_name' if not able to terminate KILL's it.
        Arguments :
            proc_name -- name of the process
            script -- when True it will search for any running script with the specified name.(default : False)
    """
    # try to terminate
    pid_t = getPID(proc_name, script)
    if pid_t == -1:
        return -1
    os.kill(pid_t, signal.SIGTERM)

    # check if terminated if not then kill.
    pid_k = getPID(proc_name, script)
    if pid_k == -1:
        return pid_t

    os.kill(pid_k, signal.SIGKILL)
    return pid_k

def getLogs(file_path, num_lines, reverse = True):
    """ Returns specifed lines from the given path.
        Arguments :
            file_path -- path to the file.
            num_lines -- number if lines to return.
            reverse -- if True : reads the file backward (default:reverse).
    """
    if os.path.exists(file_path):
        with open(file_path) as logfp:
            lines = logfp.readlines()

            if len(lines) < num_lines:
                num_lines = len(lines)

            if reverse:
                data = lines[-num_lines:]
            else:
                data = lines[:num_lines]

            return ''.join(data)

    return None

# class used to scan the wlan networking using airodump-ng
class WlanScanner:
    """ Class used to scan the wlan network using airodump-ng """

    # takes folder_name and file_name as input
    def __init__(self, folder_name, file_name):
        """ Arguments:
                folder_name -- name of the folder where the tmp files genrated will be stored.
                file_name -- name of the file in which the scan-result will be stored.
        """
        self.folder_name = "/tmp/" + folder_name
        self.file_name = file_name

    # returns name of the output file without prefix "-01.csv"
    def outputFilePath(self):
        """ Returns name of the output file without prefix '-01.csv' """
        of_path = self.folder_name + "/" + self.file_name
        return of_path

    # returns name of the output file with prefix "-01.csv"
    def resultFileName(self):
        """ Returns name of the output file with prefix "-01.csv """
        return self.outputFilePath()+"-01.csv"

    # performs some initial checks before perfoming scan.
    def initial_checks(self):
        """ Performs some initial checks before perfoming scan """

        # check if the required folder exists if not create it.
        if not os.path.isdir( self.folder_name ):
            os.makedirs(self.folder_name)

        # delete the old result file
        if os.path.exists(self.resultFileName()):
            os.remove(self.resultFileName())

    # performs the scan operation using iface interface for given number of secounds.
    def scan(self, sec, iface):
        """ performs the scan operation using iface interface for given number of secounds.
            Arguments :
                sec -- no of sec to scan for.
                iface -- name of the interface should use to scan.
        """

        self.initial_checks()

        # airodump-ng -w <path/file_name> --output-format csv --write-interval 1   <interface>
        command = ["airodump-ng", "-w", self.outputFilePath(), "--output-format", "csv", "--write-interval", "1", iface]

        airodump = sb.Popen(command, stdout=DN, stderr=DN)

        start_time = time.time()

        # wait for 'sec' number of secounds and then terminate.
        while True:
            # if Popen is not running break
            if airodump.poll() is not None:
                break

            if (time.time() - start_time) >= sec:
                airodump.terminate()

            time.sleep(1)

    # loads the result data from the scanned file and returns an csv-reader object
    def loadResultData(self):
        """ Loads the result data from the scanned file and returns an csv-reader object """

        result=[]

        if not os.path.exists(self.resultFileName()):
            return result

        with open(self.resultFileName(), "rb") as csvfile:
            csvReader = csv.reader(csvfile, delimiter=",")
            for row in csvReader:
                result.append(row)

        return result

    # parse the result from loadResultData() and returns a list containing the result
    def parseData(self):
        """ Parse the result from loadResultData() and returns a list containing the result """

        loadedData = self.loadResultData()
        loadedData = loadedData[2:-1]

        scanResults = []

        i=0
        dictAps = {}
        while i < len(loadedData):
            if len(loadedData[i]) == 0:
                break


            ap = AccessPoint(loadedData[i][0], loadedData[i][3], loadedData[i][6],
                            loadedData[i][7], loadedData[i][8], loadedData[i][13], [])

            if ap.bssid not in dictAps :
                scanResults.append(ap)
                dictAps[ ap.bssid ] = len(scanResults)-1
            i+=1

        scanResults.append( AccessPoint("(not associated)", "", "", "", "", "", []) )
        dictAps["(not associated)"] = len(scanResults)-1
        i+=1
        dictClients = {}
        while i < len(loadedData):
            if len(loadedData[i]) == 0:
                break

            client = Client(loadedData[i][0], loadedData[i][5], loadedData[i][6:])

            if client.mac not in dictClients:
                if client.bssid in dictAps:
                    scanResults[ dictAps[client.bssid] ].connected_clients.append(client)
                    dictClients[client.bssid] = 0

            i+=1

        return scanResults

# class to store info regarding an access point
class AccessPoint:
    """ Class to store info regarding an access point """

    def __init__(self, bssid, channel, cipher, auth, power, essid, connected_clients):
        self.bssid = bssid.strip()
        self.channel = channel.strip()
        self.cipher = cipher.strip()
        self.auth = auth.strip()
        self.power = power.strip()
        self.essid = essid.strip()
        self.connected_clients = connected_clients

    def __str__(self):
        result = "{ bssid : " + self.bssid + ", channel : " + self.channel + ", cipher : " + self.cipher + \
                 ", auth : " + self.auth + ", power : " + self.power + ", essid : " + self.essid + \
                 ", connected_clients : " + str(self.connected_clients) + " }"

        return result

    def toJson(self):
        """ return a json version of this class object. """

        return {
            "bssid": self.bssid,
            "channel": self.channel,
            "cipher": self.cipher,
            "auth": self.auth,
            "power": self.power,
            "essid": self.essid,
            "connected_clients": json.dumps([c.toJson() for c in self.connected_clients])
            }

# class to store info regarding an client
class Client:
    """ Class to store info regarding an client """

    def __init__(self, mac, bssid, probed_essid):
        self.mac = mac.strip()
        self.bssid = bssid.strip()
        self.probed_essids = ", ".join(probed_essid)

    def __str__(self):
        result = "{ mac : " + self.mac + ", bssid : " + self.bssid + ", probed_essids : " + self.probed_essids
        return result

    def toJson(self):
        """ return a json version of this class object. """

        return {
            "mac": self.mac,
            "bssid": self.bssid,
            "probed_essids": self.probed_essids
        }

class Deauth:
    """ Class used to perform deauth operation on an wlan network using aireplay-ng """

    # sends the deauth packets to the ap
    @staticmethod
    def deauth(packets, channel, ap_bssid, client_bssid, iface):
        """ Sends deauth packets to the AP
            Arguments:
                packets -- no of deauth packets to send.
                channel -- channel on which to send the packets.
                ap_bssid -- bssid of the AP .
                client_bssid -- bssid of the client.
                iface -- interface to be used.
        """

        # change channel.
        mon = pyw.getcard(str(iface))
        pyw.chset(mon, channel, None)
        # disconnect client from the ap.
        if client_bssid:
            # disconnects the given client from the ap.
            aireplay_deauth = sb.call(["aireplay-ng", "--deauth", str(packets), "-a", ap_bssid, "-c", client_bssid ,iface ], stdout=DN, stderr=DN)
        else:
            # disconnects all clients from the ap.
            aireplay_deauth = sb.call(["aireplay-ng", "--deauth", str(packets), "-a", ap_bssid, iface], stdout=DN, stderr=DN)


class HostapdCli():
    """ This class is a wapper for hostapd_cli """

    @staticmethod
    def isOptionEnabled(bin_path, option):
        """ Returns True if the given option is enabled by the running hostapd-mana
            Arguments :
                bin_path -- path to the hostapd_cli
                option -- option to check for.
        """

        stdout = sb.Popen([bin_path, option], stdout=sb.PIPE).stdout
        status = stdout.read()[:-1]
        if status.find("ENABLED") == -1:
            return False
        else:
            return True

    @staticmethod
    def isManaEnabled(bin_path):
        """ Returns True if the mana option is enabled in the running hostapd-mana
            Arguments :
                bin_path -- path to the hostapd_cli
        """

        return HostapdCli.isOptionEnabled(bin_path, "mana_get_state")

    @staticmethod
    def isManaLoudEnabled(bin_path):
        """ Returns True if the mana-loud option is enabled in the running hostapd-mana
            Arguments :
                bin_path -- path to the hostapd_cli
        """

        return HostapdCli.isOptionEnabled(bin_path, "mana_loud_state")

    @staticmethod
    def isMacAclEnabled(bin_path):
        """ Returns True if the mana_macacl option is enabled in the running hostapd-mana
            Arguments :
                bin_path -- path to the hostapd_cli
        """

        return HostapdCli.isOptionEnabled(bin_path, "mana_macacl_state")

    @staticmethod
    def changeOptions(bin_path, options):
        """ Change an option of the running hostapd-mana
            Arguments :
                bin_path -- path to the hostapd_cli
                option -- option to change
        """
        sb.call([bin_path, options])

    @staticmethod
    def getStaName(dnsmasq_leases, bssid):
        """ Return's a string containing name of an connected client from dnsmasq_leases file.
            returns None if not able to find.

            Arguments:
                dnsmasq_leases -- path to the dnsmasq_leases file.
                bssid -- bssid of the client to look for.
        """

        if not os.path.exists(dnsmasq_leases):
            return None

        with open(dnsmasq_leases, "r") as dlf:
            dnsmasq_leases = dlf.readlines()

        for line in dnsmasq_leases:
            info = line.split(" ")
            if bssid in info:
                return info[3]

        return None

    @staticmethod
    def getStaIp(dnsmasq_leases, bssid):
        """ Return's a string containing IP of an connected client from dnsmasq_leases file.
            returns None if not able to find.

            Arguments:
                dnsmasq_leases -- path to the dnsmasq_leases file.
                bssid -- bssid of the client to look for.
        """

        if not os.path.exists(dnsmasq_leases):
            return None

        with open(dnsmasq_leases, "r") as dlf:
            dnsmasq_leases = dlf.readlines()

        for line in dnsmasq_leases:
            info = line.split(" ")
            if bssid in info:
                return info[2]

        return None


    @staticmethod
    def listConnected(bin_path, dnsmasq_leases):
        """ Return's a list containing name of an connected client.
            Arguments:
                bin_path -- path to the hostapd_cli
                dnsmasq_leases -- path to the dnsmasq_leases file.
        """

        result = []
        if getPID("hostapd")==-1:
            return []

        stdout=sb.Popen([bin_path, "all_sta"], stdout=sb.PIPE).stdout
        sta_str = stdout.read()
        p = re.compile(r'([0-9a-f]{2}(?::[0-9a-f]{2}){5})', re.IGNORECASE)

        list_sta = re.findall( p, sta_str)

        for bssid in list_sta:
            result.append( (bssid, HostapdCli.getStaName(dnsmasq_leases, bssid), HostapdCli.getStaIp(dnsmasq_leases, bssid)) )
        return result

    @staticmethod
    def deauthConnected(bin_path, bssid):
        """ Deauths a connected client from hostapd-mana """

        sb.call([bin_path, "deauthenticate", bssid])
