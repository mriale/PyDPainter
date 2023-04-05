#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
version.py
"""
config = None

def version_set_config(config_in):
    global config
    config = config_in
    config.version = "1.0.5"
    config.copyright = "\xA92023 Mark Riale"
