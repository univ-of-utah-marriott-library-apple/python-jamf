#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import os

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
	current_version = string()
	try:
		jamf_1, jamf_2, jamf_3 = current_version.split(".")
		min_1, min_2, min_3 = min_version.split(".")
		if ( int(jamf_1) <= int(min_1) and
			 int(jamf_2) <= int(min_2) and
			 int(jamf_3) < int(min_3)):
			return current_version
	except AttributeError:
		return current_version
	return min_version
