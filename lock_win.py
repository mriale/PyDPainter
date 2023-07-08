#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import sys
import msvcrt
import os

file_path = sys.argv[1]
file_lock = open(file_path, 'a')  # Open the file

# Lock the file
try:
    msvcrt.locking(file_lock.fileno(), msvcrt.LK_NBLCK, os.path.getsize(file_path))
    data = input(f"File {sys.argv[1]} is now locked.\nPress enter to release:\n")
    
except IOError:
    print("File is already locked by another process")

finally:
    # Unlock the file
    msvcrt.locking(file_lock.fileno(), msvcrt.LK_UNLCK, os.path.getsize(file_path))
    print("File is unlocked")
    file_lock.close()


