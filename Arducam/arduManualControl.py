#!/bin/python3

from ctypes import *
import sys, os
import platform

try:
    abs_path = os.path.dirname(os.path.abspath(__file__))
    lib_name = "libarducam_config_parser.so"
    abs_lib_name = os.path.join(abs_path, lib_name)
    if os.path.exists(abs_lib_name):
        _lib = cdll.LoadLibrary(abs_lib_name)
    else:
        _lib = cdll.LoadLibrary(lib_name)
except Exception as e:
    print("Load libarducam_config_parser fail.")
    print("Make sure you have arducam_config_parser installed.")
    print("For more information, please visit: https://github.com/ArduCAM/arducam_config_parser")
    print(e)
    sys.exit(0)
