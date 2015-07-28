__author__ = 'adames'

import client
import time
import os

# How to write a deamon in python
# http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/

while True:
    monitor = client.VpnWatch()

    if monitor.vpn_is_running():
        if not monitor.server_responding():
            monitor.kill_target_prgrams()
            monitor.send_notif('vpnwatch', 'VPN connecion lost')
            exit()
    else:
        monitor.kill_target_prgrams()
        monitor.send_notif('vpnwatch', 'VPN not running')
        exit()

    time.sleep(1)