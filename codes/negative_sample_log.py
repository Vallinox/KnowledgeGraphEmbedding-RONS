#!/usr/bin/python3

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import csv
from collections import Counter


def read_log(path):
    triples = set()
    relation_counts = Counter()
    source_counts = Counter()
    mode_counts = Counter()
    rows = []

    with open(path) as fin:
        reader = csv.DictReader(fin, delimiter='\t')
        for row in reader:
            triple = (
                row['corrupted_head'],
                row['corrupted_relation'],
                row['corrupted_tail'],
            )
            triples.add(triple)
            relation_counts[row['corrupted_relation']] += 1
            source_counts[row['source']] += 1
            mode_counts[row['mode']] += 1
            rows.append(row)

    return {
        'triples': triples,
        'relations': relation_counts,
        'sources': source_counts,
        'modes': mode_counts,
        'rows': rows,
    }


def print_counts(title, counts, limit):
    print(title)
    for key, count in counts.most_common(limit):
        print('  %s: %d' % (key, count))


def summarize(args):
    log = read_log(args.log_path)
    print('Logged corrupted triples: %d' % len(log['rows']))
    print_counts('By source:', log['sources'], args.limit)
    print_counts('By mode:', log['modes'], args.limit)
    print_counts('Top corrupted relations:', log['relations'], args.limit)
    print('Examples:')
    for row in log['rows'][:args.limit]:
        print('  %s\t%s\t%s\t%s' % (
            row['corrupted_head'],
            row['corrupted_relation'],
            row['corrupted_tail'],
            row['source'],
        ))


def compare(args):
    left = read_log(args.left_log)
    right = read_log(args.right_log)

    overlap = left['triples'].intersection(right['triples'])
    only_left = sorted(left['triples'] - right['triples'])
    only_right = sorted(right['triples'] - left['triples'])

    print('%s unique corrupted triples: %d' % (
        args.left_name, len(left['triples'])
    ))
    print('%s unique corrupted triples: %d' % (
        args.right_name, len(right['triples'])
    ))
    print('overlap: %d' % len(overlap))
    print('%s only: %d' % (args.left_name, len(only_left)))
    print('%s only: %d' % (args.right_name, len(only_right)))

    print_counts('%s sources:' % args.left_name, left['sources'], args.limit)
    print_counts('%s sources:' % args.right_name, right['sources'], args.limit)
    print_counts(
        '%s top relations:' % args.left_name, left['relations'], args.limit
    )
    print_counts(
        '%s top relations:' % args.right_name, right['relations'], args.limit
    )

    print('%s-only examples:' % args.left_name)
    for triple in only_left[:args.limit]:
        print('  %s\t%s\t%s' % triple)
    print('%s-only examples:' % args.right_name)
    for triple in only_right[:args.limit]:
        print('  %s\t%s\t%s' % triple)


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description='Inspect negative-sampling logs'
    )
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    summarize_parser = subparsers.add_parser('summarize')
    summarize_parser.add_argument('--log_path', required=True)
    summarize_parser.add_argument('--limit', default=30, type=int)

    compare_parser = subparsers.add_parser('compare')
    compare_parser.add_argument('--left_log', required=True)
    compare_parser.add_argument('--right_log', required=True)
    compare_parser.add_argument('--left_name', default='left')
    compare_parser.add_argument('--right_name', default='right')
    compare_parser.add_argument('--limit', default=20, type=int)

    return parser.parse_args(args)


def main(args):
    if args.command == 'summarize':
        summarize(args)
    elif args.command == 'compare':
        compare(args)
    else:
        raise ValueError('Unknown command %s' % args.command)


if __name__ == '__main__':
    main(parse_args())
