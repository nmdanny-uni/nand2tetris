from xml.etree import ElementTree as ET
from xml.dom import minidom
from pathlib import Path
import re
import logging
import json
import dataclasses


def write_xml_file(root_elem: ET.Element, jack_file: str, suffix: str):
    """ Creates a pretty XML file for an element hierarchy created from
        a given jack file.

        :param root_elem The root XML element to be written
        :param jack_file The original .jack file that is responsible for the XML
        :param suffix Whether to append a suffix(usually T for tokenizer)
     """
    jack_path = Path(jack_file)
    file_name_no_ext = jack_path.stem
    xml_path = jack_path.parent / f"{file_name_no_ext}{suffix}.xml"

    # the following things are needed to pass the diff tests
    # prettifying the xml
    ugly_xml = ET.tostring(root_elem, 'utf-8')
    pretty_xml = minidom.parseString(ugly_xml).toprettyxml()

    # remove XML version header
    pretty_xml = re.sub(r'<\?xml .*?>\n', '', pretty_xml)

    # convert tags of the form <a /> to <a>\n</a>
    pretty_xml = re.sub(r'<(\w+)\s*/>', r'<\1>\n</\1>', pretty_xml, )

    with open(xml_path, 'w') as file:
        file.write(pretty_xml)


def write_json_file(obj: dataclasses.dataclass, jack_file: str):
    jack_path = Path(jack_file)
    file_name_no_ext = jack_path.stem
    json_path = jack_path.parent / f"{file_name_no_ext}.json"

    obj_dict = dataclasses.asdict(obj)
    js_st = json.dumps(obj_dict, indent=4)

    with open(json_path, 'w') as file:
        file.write(js_st)
