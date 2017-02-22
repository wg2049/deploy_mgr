#!/usr/bin/env  python3
# author: wugong

import configparser
import time
import datetime
import paramiko
import os
import sys
BASE_DIR= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from core import main

if __name__ == '__main__':
    main.run()








