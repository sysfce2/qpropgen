#!/usr/bin/env python3
import argparse
import os
import sys

import yaml

from jinja2 import Environment, PackageLoader


__appname__ = 'qpropgen'
__version__ = '0.1.0'
__license__ = 'Apache 2.0'

DESCRIPTION = """\
Generate QML property-based headers and implementation
"""

NO_CONST_REF_ARG_TYPES = {'int', 'bool', 'qreal'}

AUTOGENERATED_DISCLAIMER = 'This file has been generated with qpropgen, any' \
    ' changes made to it will be lost!'

HEADER_EXT = '.h'
IMPL_EXT = '.cpp'

DEFAULT_ACCESS = 'private'
VALID_ACCESS_VALUES = {'private', 'protected'}

DEFAULT_MUTABILITY = 'readwrite'


def get_filename_we(filepath):
    filename = os.path.basename(filepath)
    return os.path.splitext(filename)[0]


def complete_property(property_):
    """Adds extra fields to property_"""
    camelcase_name = property_['name'][0].upper() + property_['name'][1:]

    property_.setdefault('setter_name', 'set' + camelcase_name)

    type_ = property_['type']
    need_constref = type_ not in NO_CONST_REF_ARG_TYPES and type_[-1] != '*'
    if need_constref:
        arg_type = 'const {}&'.format(type_)
    else:
        arg_type = type_
    property_.setdefault('arg_type', arg_type)

    property_.setdefault('var_name', 'm' + camelcase_name)

    property_.setdefault('mutability', DEFAULT_MUTABILITY)

    return property_


class InvalidDefinitionError(Exception):
    pass


class ClassDefinition:
    def __init__(self, filename, dct):
        self.filename_we = get_filename_we(filename)
        self.header = self.filename_we + HEADER_EXT
        self.class_name = dct['class']['name']

        self.access = dct['class'].get('access', DEFAULT_ACCESS)
        if self.access not in VALID_ACCESS_VALUES:
            raise InvalidDefinitionError('Invalid value for access: {}'
                                         .format(self.access))

        self.properties = [complete_property(x) for x in dct['properties']]

    def generate_file(self, template, out_path):
        args = dict(
            autogenerated_disclaimer=AUTOGENERATED_DISCLAIMER,
            class_name=self.class_name,
            header=self.header,
            access=self.access,
            properties=self.properties,
        )

        with open(out_path, 'w') as f:
            f.write(template.render(**args))


def main():
    parser = argparse.ArgumentParser()
    parser.description = DESCRIPTION

    parser.add_argument('-d', '--directory', dest='directory',
                        default='.',
                        help='generate files in DIR', metavar='DIR')

    parser.add_argument('class_definition')

    args = parser.parse_args()

    with open(args.class_definition, 'r') as f:
        definition = ClassDefinition(args.class_definition, yaml.load(f))

    env = Environment(loader=PackageLoader('qpropgen', 'templates'))

    for ext in HEADER_EXT, IMPL_EXT:
        out_path = os.path.join(args.directory, definition.filename_we + ext)
        template = env.get_template('template{}'.format(ext))
        definition.generate_file(template, out_path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
# vi: ts=4 sw=4 et
