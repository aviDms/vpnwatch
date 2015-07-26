__author__ = 'adames'

import re
import os
import time
import signal
import subprocess

DOCUMENTATION = """
References:
    Get your external IP when VPN is active using ifconfig:
        http://www.cyberciti.biz/faq/how-to-find-out-the-ip-address-assigned-to-eth0-and-display-ip-only/

Logic:
    1. Get the external ip
    2. Ping the server, when conn drops, kill all apps from list
"""


class VpnWatch():

    def __init__(self, vpn_service='openvpn',
                 close_programs=['Popcorn-Time', 'transmission-gtk'],
                 verbose=False, log_file=None):

        # ip of the vpn server
        self.external_ip = self.get_external_ip()
        # processes to watch
        self.vpn_service = vpn_service
        self.vpn_service_pids = self.get_pids(vpn_service)

        # in case close_programs is passed as string
        if type(close_programs) is str:
            close_programs = close_programs.replace(',', ' ').replace(';', ' ').split()

        # get all pids from all processes that need to be killed
        self.close_programs_pids = []
        for p in close_programs:
            pids = self.get_pids(p)
            if pids:
                for pid in pids:
                    self.close_programs_pids.append(pid)

        # regex patterns
        self.ping_pattern = re.compile('(\d)% packet loss')

        if verbose:
            print 'External IP:', self.external_ip
            print 'Ping server:', self.server_responding()
            print 'VPN processes:', self.vpn_service_pids
            print 'VPN processes running:', self.vpn_is_running()
            print 'Processes to close:', self.close_programs_pids


    def __process_running(self, list_of_pids):
        """
        Return True as long as there are some processes from the list
        (process_to_watch) still running and False otherwise.
        """
        # check to see if list of pids is empty, first
        if list_of_pids:
            # cast it as a list in case one single pid si given as int
            if type(list_of_pids) is not list:
                list_of_pids = [list_of_pids]
            # in case multiple pids are given, check if they still exists
            for pid in list_of_pids:
                # if pid still exists, do nothing else return False
                if not os.path.exists(os.path.join('/proc', str(pid))):
                    return False
            return True
        else:
            return False

    def vpn_is_running(self):
        return self.__process_running(self.vpn_service_pids)

    def target_programs_are_running(self):
        return self.__process_running(self.close_programs_pids)

    def kill_target_prgrams(self):
        for pid in self.close_programs_pids:
            self.kill_process(pid)

    def server_responding(self):
        """
        Return True if ping is successful (i.e. 0% packet loss)
        or False otherwise.
        """
        # run ping command in shell, and save the output
        proc = subprocess.Popen(['ping -c 1 %s' % self.external_ip], shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        proc.stdout.close()

        # check the output for errors, if packet loss is 0, return true
        if out is '' or err is not '':
            return False
        else:
            if int(re.search(self.ping_pattern, out).group(1)) != 0:
                return  False
            else:
                return True

    @staticmethod
    def kill_process(pid):
        if os.path.exists(os.path.join('/proc', str(pid))):
            os.kill(int(pid), signal.SIGQUIT)

    @staticmethod
    def get_pids(name):
        """
        Get the pid numbers of all the processes with this name.
        :param name: name of the process you want to monitor
                     ex. openvpn, popcorn-time, ...
        :return: list of pid numbers or None in case there are no
                 active instances of this process at the moment.
        """
        try:
            return map(int, subprocess.check_output(['pidof', name]).split())
        except:
            return None

    @staticmethod
    def get_external_ip():
        """
        Function to return the external IP of this machine using the 'ifconfig'
        bash program. The output of the ifconfig command is parsed and the inet
        address of tun0 is returned as string.

        ex command:
            ifconfig -a tun0 | grep 'inet addr:' | cut -d: -f2| awk '{print $1}

        First step is to check if a tun0 connection is active, in case this is true
        the full command is run again and the output is parsed, returning the IP.
        In case the tun0 connection is not active, the function is exit returning
        False.

        :return: External IP address if tun0 is active, False otherwise
        """
        # First step, check if tun0 is active
        check = subprocess.Popen(['ifconfig', 'tun0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = check.communicate()
        check.stdout.close()
        if out is '':
            return False
        else:
            # Second step, if tun0 is active, return the ip address
            proc1 = subprocess.Popen(['ifconfig', 'tun0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc2 = subprocess.Popen(["grep 'inet addr:'"], stdin=proc1.stdout, stdout=subprocess.PIPE, shell=True)
            proc3 = subprocess.Popen(['cut -d: -f2'], stdin=proc2.stdout, stdout=subprocess.PIPE, shell=True)
            proc4 = subprocess.Popen(["awk '{ print $1}'"], shell=True, stdin=proc3.stdout,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc1.stdout.close()
            proc2.stdout.close()
            proc3.stdout.close()
            out, err = proc4.communicate()

            if out is '':
                print 'Error while getting the external IP:\n%s\n\n' % err
                print 'External IP could not be found. Please run this command in bash:'
                print "ifconfig -a tun0 | grep 'inet addr:' | cut -d: -f2| awk '{print $1}'"
            else:
                return out.strip()