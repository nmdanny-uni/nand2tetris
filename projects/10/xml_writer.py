from xml.etree.ElementTree import TreeBuilder, Element
from util import xml_to_string


class XmlWriter:
    """ Class responsible for writing an .xml file procedurally
        :param path: Output .xml file path """
    def __init__(self, path: str):
        self.__path = path
        self.__builder = TreeBuilder()

    def reset(self):
        """ Resets the writer's state """
        self.__builder = TreeBuilder()

    def flush_to_element(self) -> Element:
        """ Closes the writer and flushes its contents to a XML Element
            object """
        return self.__builder.close()

    def write_to_disk(self):
        """ Closes the writer, and flushes its contents to the .xml file """
        element = self.flush_to_element()
        xml_st = xml_to_string(element)
        with open(self.__path, 'w') as file:
            file.write(xml_st)

    def open_tag(self, tag_name: str):
        """ Opens an XML tag """
        self.__builder.start(tag_name)

    def write_leaf(self, name: str, value: str):
        """ Writes a leaf/terminal node with given tag name and value"""
        self.__builder.start(name)
        self.__builder.data(value)
        self.__builder.end(name)

    def close_tag(self, tag_name: str):
        """ Closes an XML tag """
        self.__builder.end(tag_name)


def with_xml_tag(tag_name: str):
    """ A method decorator that opens an XML tag when starting the function,
        and closes that tag when returning from the function """

    def decorator(function):
        def wrapped_parse_function(*args, **kwargs):
            self = args[0]
            # TODO cleaner way to do this?
            writer: XmlWriter = getattr(self, '_JackParser__xml_writer')
            writer.open_tag(tag_name)
            ret_type = function(*args, **kwargs)
            writer.close_tag(tag_name)
            return ret_type

        return wrapped_parse_function

    return decorator

