# WiFiAce
>WiFi ACE is a simplified web interface that allows the security analyst to audit the wireless networks stealthy using raspberry pi.

Apart from raspberry pi WifiAce works on any linux based operating system that meets the below requirements.
![Dashboard](https://2.bp.blogspot.com/-BSsbeKiQobg/WrKiaDWvMcI/AAAAAAAAIjw/BAIbVIF2Bo8NDbSOGj5OJ5e2as5aHLG7wCLcBGAs/s640/Screenshot%2Bat%2B2018-03-15%2B10-58-02.png)
## Features 
 * **_Scanning_** - Allows scanning of the vicinity and gather information about the devices.
 * **_Rouge Access Point_** - With the help of hostapd-mana combined with **Karma** and **MANA** attacks.
 * **_Modular_** - Easy to create plugin to extend the functionality on the go.
 * **_Easy to use_** - No tricky commands to remember simplified and responsive web interface.
 * **_Accessiblity_** - Can be easily accessed from any device in the current network.

#### Requirements
  * aircrack-ng
  * subversion
  * python-apt
  * hostapd-mana

## Installing wifiace :

### Using Script
WiFi can be easily installed on any debian based OS by running the ````setup.py```` script. 
Remember to clone repository using ````--recursive```` option.

### Manually 

To install wifiACE manually install the equivalent packages mentioned in the requirements and follow the following steps.
```sh
$ git clone --recursive https://github.com
$ cd wifiace/
$ pip install -r requirements.txt 
$ sudo cp config/default/wifiace.conf /etc/
```
#### Hostapd-mana requirements
- libssl1.0-dev  
- bridge-utils 
- libnl-genl-3-dev

#### Building hostapd-mana
Follow the below steps and build **hostapd-mana**.
```sh
$ cd external_tools/hostapd-mana/hostapd
$ make
```
## WifiACE with Raspberry Pi
<img src="https://bitbucket.org/repo/EgRE9Rb/images/3104941646-IMG_20180505_165020.jpg" width=500 />

WifiACE can work very well similar to WiFi Pineapple®. Work's perfectly with Kali and Parrotsec on rpi. Just run the setup script and select *yes* when it asks to add WifiACE to *crontab* and enable *USB tethering*.
##### Note : Note : If you are using any OS other than Parrotsec or Kali, following the steps given in the [Manual installation](#manually) and the following steps for startup support and USB tethering.
#
#

#### crontab for WifiACE
You can make following changes to start WifiACE on boot. Add this line as **root** user to your crontabs(**crontab -e**).
```sh
@reboot /path/to/wifiace/directory/wifiace.py &
```
#### USB tethering
Allows you to share internet of your smartphone with rpi. Add following lines to **/etc/network/interfaces**
```sh
#USB tethering config for wifiace
allow-hotplug usb0
iface usb0 inet static
address 192.168.42.1
netmask 255.255.255.0
```

### Launching WifiAce
WiFiAce requires ```root``` privilages for running. By default WIfiACE is accessible from http://127.0.0.1:5000 from your browser,if you have enabled USB tethering option then it is also accessible from http://192.168.42.1:5000 on your mobile device or else if you wish can change IP and Port while launching. The default ID and password is ```root:toor```.

Following are the launch options for *wifiace*. 
```
# python wifiace.py -h
usage: wifiace [-h] [-a HOST] [-p PORT] [-D]

This script starts flask server and deploys wifiace-web on it.

optional arguments:
  -h, --help            show this help message and exit
  -a HOST, --host HOST  IP address on which the server should bind leave it
                        blank to bind to localhost
  -p PORT, --port PORT  port for the webserver to run on (Default : 5000)
  -D, --debug           Starts wifiace in debug mode.(Warning:Instace checking
                        doesn't work in this mode.)

```
If you want to know more about *wifiace* please refer the [wiki](https://github.com/wifiace/wifiace/wiki).
