# -*- coding: utf-8 -*-
# flake8: noqa

"""
python-jamf
Module to hit the Jamf API
"""

from . import convert, version
from .admin import JamfAdmin as Admin
from .api import API
from .records import *
from .server import Server
