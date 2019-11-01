""" This module contains some general purpose functions """
from xml.etree import ElementTree as ET
from xml.dom import minidom
from pathlib import Path
import re
import logging
import json
import dataclasses


def change_extension(path: str, ext: str) -> str:
    """ Given a path to a file, returns a path to the same file but with
        a different extension """
    path = Path(path)
    path_no_ext = path.stem
    return str(path.parent / f"{path_no_ext}.{ext}")


def xml_to_string(root: ET.Element) -> str:
    """ Converts an XML node to string, also prettifying it and
        ensuring it complies with diff tests"""
    # prettifying the xml
    ugly_xml = ET.tostring(root, 'utf-8')
    pretty_xml = minidom.parseString(ugly_xml).toprettyxml()

    # remove XML version header
    pretty_xml = re.sub(r'<\?xml .*?>\n', '', pretty_xml)

    # convert tags of the form <a /> to <a>\n</a>
    pretty_xml = re.sub(r'<(\w+)\s*/>', r'<\1>\n</\1>', pretty_xml)

    return pretty_xml


def dataclass_to_json_string(obj: dataclasses.dataclass) -> str:
    """ Converts a 'dataclass' object(similar to named tuple) to json, for
        debugging purposes """
    dic = dataclasses.asdict(obj)
    return json.dumps(dic, indent=4)

