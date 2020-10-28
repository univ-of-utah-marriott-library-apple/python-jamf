# -*- coding: utf-8 -*-

"""
XML and JSON data conversion functions
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2019 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "0.2.2"

from xml.etree import cElementTree as ElementTree
import xml.sax.saxutils
from collections import defaultdict


class Error(Exception):
    """ just passing through """
    pass


def etree_to_dict(elem):
    """
    converts xml.cElementTree to python dict
    adapted from: https://stackoverflow.com/a/10077069/12020818
    removed attribute support
    """
    result = {elem.tag: None}
    children = list(elem)
    if children:
        defd = defaultdict(list)
        for dct in map(etree_to_dict, children):
            for key, val in dct.items():
                defd[key].append(val)
        result = {
            elem.tag: {
                key:val[0] if len(val) == 1 else val for key, val in defd.items()
            }
        }
    elif elem.text:
        result[elem.tag] = elem.text.strip()
    return result


def dict_to_xml(data):
    """
    Convert python dict to xml string
    :returns:  xml string
    """
    if isinstance(data, dict):
        xml_str = ''
        for key, value in data.items():
            if value is None:
                xml_str += f"<{key}/>"
            elif isinstance(value, list):
                # if the value is a list, wrap each entry with the key
                for i in value:
                    result = dict_to_xml(i)
                    xml_str += f"<{key}>{result}</{key}>"
            else:
                # otherwise, wrap the entire result
                result = dict_to_xml(value)
                xml_str += f"<{key}>{result}</{key}>"
    elif isinstance(data, list):
        raise Error("unable to properly tag nested lists")
    else:
        # string, boolean, integers, floats, etc
        xml_str = xml.sax.saxutils.escape(f"{data}")

    return xml_str


def xml_to_dict(xml_string):
    """
    Convert xml string to python dict
    :returns:  dict
    """
    root = ElementTree.XML(xml_string)
    return etree_to_dict(root)
