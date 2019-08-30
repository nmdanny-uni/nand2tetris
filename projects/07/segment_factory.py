""" This module manages segment objects, and is responsible for assigning
    correct Segment instances when parsing commands. (For example, separate
    'StaticSegment' instances for different files, but the rest of the segments
    are shared)
"""
from model import Segment, ConstantSegment, StaticSegment, CompilationError
from pathlib import Path


class SegmentFactory:
    """ Allows access to segment objects via file name and segment type """

    def __init__(self):
        self.__segments = {
            "argument": Segment("argument", "ARG"),
            "local": Segment("local", "LCL"),
            "constant": ConstantSegment(),
            "pointer": Segment("pointer", "THIS", indirection=False),
            "this": Segment("this", "THIS"),
            "that": Segment("that", "THAT"),
            "temp": Segment("temp", "R5", indirection=False)
        }
        self.__static_segments = {}

    def get_segment(self, file_name: str, segment_name: str) -> Segment:
        """ Gets the segment of given name for given file. Raises error on
            invalid segment """
        if segment_name in self.__segments:
            return self.__segments[segment_name]
        if segment_name == "static":
            stripped_name = Path(file_name).stem
            return self.__static_segments.get(stripped_name,
                                              StaticSegment(stripped_name))
        raise CompilationError(f"Non-existent segment \"{segment_name}\"")
