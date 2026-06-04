#!/usr/bin/python3

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
from collections import defaultdict

import numpy as np


class JenaMaterializedReasoner(object):
    '''
    Use Apache Jena materialized files to generate corrupted entities.

    Expected files in cache_path:
      * entity_types.tsv: entity_name<TAB>class_uri
      * relation_domain.tsv: relation_name<TAB>class_uri
      * relation_range.tsv: relation_name<TAB>class_uri
      * disjoint_classes.tsv: class_uri<TAB>class_uri
      * functional_relations.tsv: relation_name
      * inverse_functional_relations.tsv: relation_name
      * irreflexive_relations.tsv: relation_name
    '''

    def __init__(self, cache_path, triples, entity2id, relation2id):
        self.nentity = len(entity2id)
        self.relation_domain = defaultdict(set)
        self.relation_range = defaultdict(set)
        self.disjoint_classes = defaultdict(set)
        self.functional_relations = set()
        self.inverse_functional_relations = set()
        self.irreflexive_relations = set()
        self.entity_types = defaultdict(set)

        self._read_relation_classes(
            os.path.join(cache_path, 'relation_domain.tsv'),
            relation2id,
            self.relation_domain
        )
        self._read_relation_classes(
            os.path.join(cache_path, 'relation_range.tsv'),
            relation2id,
            self.relation_range
        )
        self._read_disjoint_classes(
            os.path.join(cache_path, 'disjoint_classes.tsv')
        )
        self._read_functional_relations(
            os.path.join(cache_path, 'functional_relations.tsv'),
            relation2id
        )
        self._read_relation_set(
            os.path.join(cache_path, 'inverse_functional_relations.tsv'),
            relation2id,
            self.inverse_functional_relations,
            required=False
        )
        self._read_relation_set(
            os.path.join(cache_path, 'irreflexive_relations.tsv'),
            relation2id,
            self.irreflexive_relations,
            required=False
        )
        self._read_entity_types(
            os.path.join(cache_path, 'entity_types.tsv'),
            entity2id
        )

        self._infer_entity_types_from_schema(triples)
        self.invalid_head = self._build_invalid_entity_pools(self.relation_domain)
        self.invalid_tail = self._build_invalid_entity_pools(self.relation_range)
        self.all_entities = np.arange(self.nentity, dtype=np.int64)

    def _read_relation_classes(self, path, relation2id, target):
        if not os.path.exists(path):
            self._raise_missing_file(path)

        with open(path) as fin:
            for line in fin:
                relation, relation_class = line.rstrip('\n').split('\t', 1)
                relation_id = relation2id.get(relation)
                if relation_id is not None:
                    target[relation_id].add(relation_class)

    def _read_disjoint_classes(self, path):
        if not os.path.exists(path):
            self._raise_missing_file(path)

        with open(path) as fin:
            for line in fin:
                first_class, second_class = line.rstrip('\n').split('\t', 1)
                self.disjoint_classes[first_class].add(second_class)
                self.disjoint_classes[second_class].add(first_class)

    def _read_functional_relations(self, path, relation2id):
        self._read_relation_set(path, relation2id, self.functional_relations)

    def _read_relation_set(self, path, relation2id, target, required=True):
        if not os.path.exists(path):
            if required:
                self._raise_missing_file(path)
            return

        with open(path) as fin:
            for line in fin:
                relation = line.rstrip('\n')
                relation_id = relation2id.get(relation)
                if relation_id is not None:
                    target.add(relation_id)

    def _read_entity_types(self, path, entity2id):
        if not os.path.exists(path):
            self._raise_missing_file(path)

        with open(path) as fin:
            for line in fin:
                entity, entity_class = line.rstrip('\n').split('\t', 1)
                entity_id = entity2id.get(entity)
                if entity_id is not None:
                    self.entity_types[entity_id].add(entity_class)

    def _raise_missing_file(self, path):
        cache_path = os.path.dirname(path)
        dataset_path = os.path.dirname(cache_path)
        ontology_path = os.path.join(dataset_path, 'ontology.ttl')
        raise ValueError(
            'Missing Jena materialization file: %s\n'
            'Create the Jena cache before training, for example:\n'
            '  python codes/materialize_with_jena.py '
            '--data_path %s --ontology_path %s --output_path %s\n'
            'This requires a local JDK and Maven installation.'
            % (path, dataset_path, ontology_path, cache_path)
        )

    def _infer_entity_types_from_schema(self, triples):
        for head, relation, tail in triples:
            self.entity_types[head].update(self.relation_domain[relation])
            self.entity_types[tail].update(self.relation_range[relation])

    def _build_invalid_entity_pools(self, relation_constraints):
        pools = {}
        for relation, required_classes in relation_constraints.items():
            incompatible_classes = set()
            for required_class in required_classes:
                incompatible_classes.update(self.disjoint_classes[required_class])

            invalid_entities = [
                entity
                for entity, entity_types in self.entity_types.items()
                if entity_types.intersection(incompatible_classes)
            ]
            pools[relation] = np.asarray(invalid_entities, dtype=np.int64)
        return pools

    def negative_entities(self, head, relation, tail, mode):
        if mode == 'head-batch':
            invalid_head = self.invalid_head.get(
                relation, np.empty(0, dtype=np.int64)
            )
            if relation in self.inverse_functional_relations:
                invalid_head = np.union1d(invalid_head, self.all_entities)
            if relation in self.irreflexive_relations:
                invalid_head = np.union1d(
                    invalid_head, np.asarray([tail], dtype=np.int64)
                )
            return invalid_head
        elif mode == 'tail-batch':
            invalid_tail = self.invalid_tail.get(
                relation, np.empty(0, dtype=np.int64)
            )
            if relation in self.functional_relations:
                invalid_tail = np.union1d(invalid_tail, self.all_entities)
            if relation in self.irreflexive_relations:
                invalid_tail = np.union1d(
                    invalid_tail, np.asarray([head], dtype=np.int64)
                )
            return invalid_tail
        else:
            raise ValueError('Training batch mode %s not supported' % mode)

    def summary(self):
        return {
            'domain_relations': len(self.relation_domain),
            'range_relations': len(self.relation_range),
            'disjoint_classes': len(self.disjoint_classes),
            'functional_relations': len(self.functional_relations),
            'inverse_functional_relations': len(
                self.inverse_functional_relations
            ),
            'irreflexive_relations': len(self.irreflexive_relations),
            'typed_entities': len(self.entity_types),
        }
