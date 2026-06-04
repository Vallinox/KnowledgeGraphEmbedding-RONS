#!/usr/bin/python3

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
from collections import defaultdict
from urllib.parse import quote


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description='Generate a conservative RDF/OWL ontology from KGE triples'
    )
    parser.add_argument('--data_path', required=True, help='Dataset directory')
    parser.add_argument(
        '--output_path',
        default=None,
        help='Output Turtle file. Defaults to <data_path>/ontology.ttl'
    )
    parser.add_argument(
        '--infer_functional_properties',
        action='store_true',
        help='Infer owl:FunctionalProperty from observed training triples'
    )
    parser.add_argument(
        '--infer_inverse_functional_properties',
        action='store_true',
        help='Infer owl:InverseFunctionalProperty from observed training triples'
    )
    parser.add_argument(
        '--min_functional_support',
        default=20,
        type=int,
        help='Minimum distinct heads required to infer a functional property'
    )
    return parser.parse_args(args)


def read_relations(data_path):
    relations = []
    with open(os.path.join(data_path, 'relations.dict')) as fin:
        for line in fin:
            _, relation = line.rstrip('\n').split('\t', 1)
            relations.append(relation)
    return relations


def read_train_triples(data_path):
    triples = []
    with open(os.path.join(data_path, 'train.txt')) as fin:
        for line in fin:
            head, relation, tail = line.rstrip('\n').split('\t')
            triples.append((head, relation, tail))
    return triples


def turtle_literal(value):
    return '"%s"' % (
        value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    )


def resource_uri(resource_type, value):
    return '<urn:kge:%s:%s>' % (resource_type, quote(value, safe=''))


def generate_ontology(
        relations, triples, infer_functional_properties=False,
        infer_inverse_functional_properties=False,
        min_functional_support=20):
    heads = defaultdict(set)
    tails = defaultdict(set)
    tails_by_head = defaultdict(lambda: defaultdict(set))
    heads_by_tail = defaultdict(lambda: defaultdict(set))

    for head, relation, tail in triples:
        heads[relation].add(head)
        tails[relation].add(tail)
        tails_by_head[relation][head].add(tail)
        heads_by_tail[relation][tail].add(head)

    lines = [
        '# Generated heuristically from observed training triples.',
        '# Review these axioms before using them as domain knowledge.',
        '@prefix owl: <http://www.w3.org/2002/07/owl#> .',
        '@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .',
        '',
    ]

    for relation in relations:
        relation_uri = resource_uri('relation', relation)
        domain_uri = resource_uri('class:domain', relation)
        range_uri = resource_uri('class:range', relation)
        relation_types = []

        relation_heads = heads[relation]
        relation_tails = tails[relation]
        is_functional = (
            infer_functional_properties
            and len(relation_heads) >= min_functional_support
            and all(
                len(head_tails) == 1
                for head_tails in tails_by_head[relation].values()
            )
        )
        if is_functional:
            relation_types.append('owl:FunctionalProperty')
        is_inverse_functional = (
            infer_inverse_functional_properties
            and len(relation_tails) >= min_functional_support
            and all(
                len(tail_heads) == 1
                for tail_heads in heads_by_tail[relation].values()
            )
        )
        if is_inverse_functional:
            relation_types.append('owl:InverseFunctionalProperty')

        lines.append('%s' % relation_uri)
        if relation_types:
            lines.append('    a %s ;' % ', '.join(relation_types))
        lines.extend([
            '    rdfs:label %s ;' % turtle_literal(relation),
            '    rdfs:domain %s ;' % domain_uri,
            '    rdfs:range %s .' % range_uri,
        ])
        if relation_heads and relation_tails and relation_heads.isdisjoint(relation_tails):
            lines.extend([
                '',
                '%s owl:disjointWith %s .' % (domain_uri, range_uri),
            ])
        lines.append('')

    return '\n'.join(lines)


def main(args):
    output_path = args.output_path or os.path.join(args.data_path, 'ontology.ttl')
    relations = read_relations(args.data_path)
    triples = read_train_triples(args.data_path)
    ontology = generate_ontology(
        relations,
        triples,
        infer_functional_properties=args.infer_functional_properties,
        infer_inverse_functional_properties=(
            args.infer_inverse_functional_properties
        ),
        min_functional_support=args.min_functional_support,
    )

    with open(output_path, 'w') as fout:
        fout.write(ontology)

    print('Generated %s from %d relations and %d triples' % (
        output_path, len(relations), len(triples)
    ))


if __name__ == '__main__':
    main(parse_args())
