#!/usr/bin/python3

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import shutil
import subprocess


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description='Run the Apache Jena materializer from Python'
    )
    parser.add_argument('--data_path', required=True, help='Dataset directory')
    parser.add_argument('--ontology_path', required=True, help='Ontology TTL file')
    parser.add_argument(
        '--output_path',
        required=True,
        help='Directory where Jena TSV files will be written'
    )
    return parser.parse_args(args)


def main(args):
    mvn = shutil.which('mvn')
    if mvn is None:
        raise ValueError(
            'Maven was not found. Install maven!'
        )

    root_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir)
    )
    project_path = os.path.join(root_path, 'jena-materializer')
    data_path = os.path.abspath(args.data_path)
    ontology_path = os.path.abspath(args.ontology_path)
    output_path = os.path.abspath(args.output_path)
    os.makedirs(output_path, exist_ok=True)

    command = [
        mvn,
        '-q',
        'compile',
        'exec:java',
        '-Dexec.args=%s %s %s' % (data_path, ontology_path, output_path),
    ]
    subprocess.check_call(command, cwd=project_path)


if __name__ == '__main__':
    main(parse_args())
