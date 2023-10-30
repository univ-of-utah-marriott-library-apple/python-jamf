# -*- coding: utf-8 -*-

"""
XML and JSON data conversion functions
"""

__author__ = "Sam Forester"
__email__ = "sam.forester@utah.edu"
__copyright__ = "Copyright (c) 2019 University of Utah, Marriott Library"
__license__ = "MIT"
__version__ = "0.2.2"

import xml.sax.saxutils
from collections import defaultdict
from xml.etree import cElementTree as ElementTree


class Error(Exception):
    """just passing through"""

    pass


def etree_to_dict(elem, plurals):
    """
    converts xml.cElementTree to python dict
    adapted from: https://stackoverflow.com/a/10077069/12020818
    removed attribute support
    """
    result = {elem.tag: None}
    plurals2 = None
    is_list = False
    if plurals is not None and elem.tag in plurals:
        if type(plurals[elem.tag]) is not list:
            plurals2 = plurals[elem.tag]
    children = list(elem)
    if children:
        child_dict = defaultdict(list)
        has_size = False
        for child in children:
            if child.tag == "size":
                has_size = True
            converted = etree_to_dict(child, plurals2)
            if converted != {"size": "0"}:
                for key, val in converted.items():
                    child_dict[key].append(val)
        result = {}
        for key, val in child_dict.items():
            #             print(f"{key}, {val[0]}, {type(val[0])}, {has_size}")
            if not is_list:
                is_list = len(val) > 1 or (has_size and type(val[0]) is dict)
            if elem.tag not in result:
                result[elem.tag] = {}
            force_str = False
            if plurals is not None and elem.tag in plurals and key in plurals[elem.tag]:
                if type(plurals[elem.tag][key]) is list:
                    is_list = True
                elif type(plurals[elem.tag][key]) is str:
                    force_str = True
            if not force_str and is_list:
                result[elem.tag][key] = val
            else:
                result[elem.tag][key] = val[0]
    elif elem.text:
        result[elem.tag] = elem.text.strip()
    return result


def dict_to_xml(data):
    """
    Convert python dict to xml string
    :returns:  xml string
    """
    if isinstance(data, dict):
        xml_str = ""
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


def xml_to_dict(xml_string, plurals=None):
    """
    Convert xml string to python dict
    :returns:  dict
    """
    root = ElementTree.XML(xml_string)
    return etree_to_dict(root, plurals)
