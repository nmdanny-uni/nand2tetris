""" Entry point to the program """
import argparse
import logging
from pathlib import Path

from jack_parser import JackParser
from jack_compiler import JackCompiler
from tokenizer import Tokenizer
from xml_writer import XmlWriter
from vm_writer import  VMWriter
from util import change_extension

# parsed program arguments, see main for possibilities
args = None


class JackAnalyzer:
    """ Responsible for driving the compilation process of a jack file or
        directory """
    def __init__(self, path: str):
        """ Creates an analyzer for a .jack file, or a folder containing
            a jack program. """
        self.__files = []
        if Path(path).is_file():
            self.__files.append(path)
        else:
            self.__files.extend(list(Path(path).glob("*.jack")))

    @staticmethod
    def process_file(jack_file: str):
        """ Processes a single .jack file, parsing it, emitting xml(if ex10),
            and then compiling and emitting vm(if ex11)"""
        tokenizer = Tokenizer(jack_file)
        xml_writer = XmlWriter(change_extension(jack_file, "xml"))
        tokens = list(tokenizer.iter_tokens())
        engine = JackParser(tokens, xml_writer)

        clazz = engine.parse_class()

        # emit .xml either if we're in ex10(no compile flag) or if we are
        # debugging
        if not args.compile or args.verbose:
            xml_writer.write_to_disk()

        if args.compile:
            vm_writer = VMWriter(change_extension(jack_file, "vm"))
            compiler = JackCompiler(vm_writer, clazz)
            compiler.compile_class()
            vm_writer.close()

    def run(self):
        """ Runs the analyzer, emitting XML and/or JSON files
            depending on the program's args. """
        for file in self.__files:
            try:
                JackAnalyzer.process_file(file)

            except Exception as ex:
                logging.error(f"Encountered error while processing '{file}')")
                logging.exception(ex)
                raise


def main():
    """ Entry point to program, with support for extra debugging flags if needed """
    argparser = argparse.ArgumentParser(description="Jack analyzer")
    argparser.add_argument(
        'input',
        help='A .jack file, or a directory with .jack files')

    # in this mode, .xml is always emitted, regardless of the compile
    # flag, and extra debug info is printed in the emitted .vm files as well as
    # standard output. (via 'logging.debug' calls)
    argparser.add_argument('-v', '--verbose',
                           action='store_true',
                           help='print debug information')

    # switches between ex10(no flag) and ex11(with flag). When on, XML isn't
    # emitted and we also perform the compilation step.
    argparser.add_argument('-c', '--compile',
                           action='store_true',
                           help='emit .vm instead of .xml')
    global args
    args = argparser.parse_args()

    # ensure debug prints are only printed in verbose mode
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.ERROR)

    analyzer = JackAnalyzer(args.input)
    analyzer.run()


if __name__ == '__main__':
    main()
