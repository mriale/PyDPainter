#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import sys
import fcntl
import os

file_path = sys.argv[1]
file_lock = open(file_path, 'a')  # Open the file

# Lock the file (fcntl.F_LOCK)
try:
    fcntl.flock(file_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    data = input(f"File {sys.argv[1]} is now locked.\nPress enter to release:\n")
    
except IOError:
    print("File is already locked by another process")

finally:
    # Unlock the file (fcntl.F_UNLOCK)
    fcntl.flock(file_lock.fileno(), fcntl.LOCK_UN)
    print("File is unlocked")
    file_lock.close()


