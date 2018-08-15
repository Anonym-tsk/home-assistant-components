import os

from subprocess import STDOUT, check_call

DOMAIN = 'libusb'

def setup(hass, config):
    check_call(['apt-get', 'update'], stdout=open(os.devnull, 'wb'), stderr=STDOUT)
    check_call(['apt-get', 'install', '-y', 'libusb-1.0-0-dev'], stdout=open(os.devnull, 'wb'), stderr=STDOUT)

    return True
