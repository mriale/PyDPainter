#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
version.py
"""
config = None

def version_set_config(config_in):
    global config
    config = config_in
    config.version = "2.2.1 beta"
    config.copyright = "\xA92025 Mark Riale"
