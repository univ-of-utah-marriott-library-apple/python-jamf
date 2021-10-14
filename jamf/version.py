#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import os
import re

__all__ = (
    'string',
    'jamf_version_up_to'
)

def string():
    try:
        with open(os.path.dirname(__file__) + "/VERSION", "r", encoding="utf-8") as fh:
            version = fh.read().strip()
            if version:
                return version
    except:
        pass
    return "0.0.0"


def jamf_version_up_to(min_version):
    full_version = string()
    try:
        m = re.match(r"^([0-9]+)\.([0-9]+)\.([0-9]+)", full_version)
        min1, min2, min3 = min_version.split(".")
        if ( int(m.group(1)) >= int(min1) and
             int(m.group(2)) >= int(min2) and
             int(m.group(3)) >= int(min3)):
            return min_version # Pass
    except AttributeError:
        return full_version # Fail
    return full_version # Fail
