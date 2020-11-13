# -*- coding: utf-8 -*-

"""
python-jamf
Module to hit the Jamf API
"""

from .api import API
from .admin import JamfAdmin as Admin
from . import package
from . import convert
from .records import *

__version__ = "0.4.2"