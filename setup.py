from os.path import isdir,isfile,dirname,abspath
from subprocess import call,check_call,CalledProcessError
from os import getcwd,chdir,getuid
from ConfigParser import ConfigParser

def check_firejail():
	#check if firejail is installed or not
	print "[INFO]Checking Firejail"
	
	if isfile("/usr/bin/firejail"):
	
		ans = raw_input("Firejail is installed\n,Wifiace currently doesn't work with firejail do you want to remove it ?[Y/n]")
	

		if ans.lower()=="y" or ans=="":
	
			try :
				check_call("apt update && apt remove firejail -y",shell=True)
	
			except CalledProcessError :
				print "[ERROR]Something went wrong while installing dependency please fix and rerun the setup."
	
			except OSError:
				print "The script only support debian based systems."
				exit(2)
	
		elif ans.lower()=="n":
			print "[ERROR]Setup cannot continue."
			exit(2)
	
		else :
			print "[ERROR]Invalid option."
			exit(2)


def install_apt_pip():
	#checks and install apt and pip packages
	print "[INFO]Installing dependency"
	
	try :	
		check_call("apt install aircrack-ng subversion python-pip python-apt -y dnsmasq macchanger",shell=True)
	
	except CalledProcessError :
		print "[ERROR]Something went wrong while installing dependency please fix and rerun the setup."
		exit(3)
	
	try :
		check_call("pip install -r requirements.txt",shell=True)
	
	except CalledProcessError :
		print "[ERROR]Something went wrong while installing pythong packages please fix and rerun the setup."
		exit(3)


def hostapd_check():
	
	#checks the hostapd installation and update submodule if not done
	if isfile("external_tools/hostapd-mana/hostapd/hostapd") and isfile("external_tools/hostapd-mana/hostapd/hostapd_cli"):
		print "[INFO]Hostapd is already installed."
	
	else :
		call("git submodule init && git submodule update",shell=True)
		build_hostapd()

def build_hostapd():
	#downloads packages for hostapd and starts building it
	print "[INFO]Installing hostapd-mana dependency"
	
	try :
		check_call("apt-get install libssl1.0-dev bridge-utils libnl-genl-3-dev -y",shell=True)
	
	except CalledProcessError :
		print "[ERROR]Something went wrong while installing dependency please fix and rerun the setup."
		exit(3)
	
	chdir("external_tools/hostapd-mana/hostapd/")
	call("make",shell=True)

def set_conf():
	print "[INFO]Setting up config file."
	
	pwd = dirname(abspath(__file__))
	
	print pwd
	
	etc_path = "/etc/wifiace.conf"
	
	chdir(pwd)
	
	if isfile("/etc/wifiace.conf"):
		pass
	else :
		call("cp config/default/wifiace.conf /etc/",shell=True)

	conf = ConfigParser()
	conf.read(etc_path)
	conf.set("core","install_dir",pwd)

	with open(etc_path,"wb") as conf_file :
		conf.write(conf_file)

	print "[INFO]Setting Wifiace in {}".format(pwd)

def set_cron():

	ans = raw_input("Do you want to start wifiace on system startup ?[y/N] : ")
	
	pwd = dirname(abspath(__file__)) + "/wifiace.py"
	
	if ans.lower()=="n" or ans=="" :
	
		return 0
	
	elif ans.lower()=="y" :
		
		try :
	
			with open("/var/spool/cron/crontabs/root","r") as file :
				if "wifiace.py" in file.read():	
					print "[INFO]Looks like wifiace is already set in cron job skipping ..."
		except IOError :
				with open("/var/spool/cron/crontabs/root","a") as file :
					file.write("\n@reboot " + pwd + " & \n")
	else :
		print "[ERROR]Invalid Input"

def set_hotplugs():
	ans = raw_input("Do want to add usb tethering support ? [y/N] : ")

	if ans.lower()=="y" :
		with open("/etc/network/interfaces","a+") as file :
			if "wifiace" in file.read() :
				return 0
			else :
				print "[INFO]Setting up USB tethering."
				file.write("#USB tethering config for wifiace")
				file.write("\nallow-hotplug usb0\niface usb0 inet static\n")
				file.write("address 192.168.42.1\nnetmask 255.255.255.0\n")
				print "[INFO]Done setting up USB tethering."
	elif ans.lower()=="" or ans.lower()=="n" :
		return 0
	else :
		print "[ERROR]Invalid Input"
def main():
	check_firejail()
	install_apt_pip()
	hostapd_check()
	set_conf()
	set_cron()
	set_hotplugs()

if __name__ == '__main__':
	if getuid()!=0:
		print "[WARNING]Please execute script as root."
		exit(4)
	if "wifiace" not in getcwd():
		print "[WARNING]Please execute Script only in wifiace directory."
		exit(5)
	main()
