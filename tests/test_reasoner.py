#!/usr/bin/python3

import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'codes'))

from generate_ontology import generate_ontology
from reasoner import JenaMaterializedReasoner

try:
    from dataloader import TrainDataset
except ImportError:
    TrainDataset = None


ONTOLOGY = '''
@prefix ex: <http://example.org/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ex:Person owl:disjointWith ex:Organization .

ex:worksFor
    a owl:FunctionalProperty ;
    rdfs:domain ex:Person ;
    rdfs:range ex:Organization .

ex:hasId
    a owl:InverseFunctionalProperty ;
    rdfs:domain ex:Person ;
    rdfs:range ex:Organization .

ex:knows
    a owl:IrreflexiveProperty ;
    rdfs:domain ex:Person ;
    rdfs:range ex:Person .

ex:visits
    rdfs:domain ex:Person ;
    rdfs:range ex:Organization .

ex:alice a ex:Person .
ex:bob a ex:Person .
ex:otherOrg a ex:Organization .
'''


class JenaReasonerTest(unittest.TestCase):
    def setUp(self):
        self.entity2id = {
            'http://example.org/alice': 0,
            'http://example.org/bob': 1,
            'http://example.org/acme': 2,
            'http://example.org/otherOrg': 3,
        }
        self.relation2id = {
            'http://example.org/worksFor': 0,
            'http://example.org/visits': 1,
            'http://example.org/hasId': 2,
            'http://example.org/knows': 3,
        }
        self.triples = [
            (0, 0, 2),
            (0, 1, 2),
            (0, 2, 2),
            (0, 3, 1),
        ]
        ontology_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.ttl', delete=False
        )
        ontology_file.write(ONTOLOGY)
        ontology_file.close()
        self.ontology_path = ontology_file.name
        self.reasoner = self._build_jena_reasoner()

    def tearDown(self):
        os.unlink(self.ontology_path)

    def _build_jena_reasoner(self):
        cache_dir = tempfile.TemporaryDirectory()
        self.addCleanup(cache_dir.cleanup)

        files = {
            'relation_domain.tsv': (
                'worksFor\thttp://example.org/Person\n'
                'visits\thttp://example.org/Person\n'
                'hasId\thttp://example.org/Person\n'
                'knows\thttp://example.org/Person\n'
            ),
            'relation_range.tsv': (
                'worksFor\thttp://example.org/Organization\n'
                'visits\thttp://example.org/Organization\n'
                'hasId\thttp://example.org/Organization\n'
                'knows\thttp://example.org/Person\n'
            ),
            'disjoint_classes.tsv': (
                'http://example.org/Person\t'
                'http://example.org/Organization\n'
            ),
            'functional_relations.tsv': 'worksFor\n',
            'inverse_functional_relations.tsv': 'hasId\n',
            'irreflexive_relations.tsv': 'knows\n',
            'entity_types.tsv': (
                'http://example.org/alice\thttp://example.org/Person\n'
                'http://example.org/bob\thttp://example.org/Person\n'
                'http://example.org/acme\thttp://example.org/Organization\n'
                'http://example.org/otherOrg\t'
                'http://example.org/Organization\n'
            ),
        }
        for filename, content in files.items():
            with open(os.path.join(cache_dir.name, filename), 'w') as fout:
                fout.write(content)

        return JenaMaterializedReasoner(
            cache_dir.name,
            self.triples,
            self.entity2id,
            {
                'worksFor': 0,
                'visits': 1,
                'hasId': 2,
                'knows': 3,
            },
        )

    def test_domain_and_inferred_range_generate_invalid_heads(self):
        candidates = self.reasoner.negative_entities(0, 1, 2, 'head-batch')
        self.assertEqual({2, 3}, set(candidates))

    def test_range_generates_invalid_tails(self):
        candidates = self.reasoner.negative_entities(0, 1, 2, 'tail-batch')
        self.assertEqual({0, 1}, set(candidates))

    def test_functional_property_generates_alternative_tails(self):
        candidates = self.reasoner.negative_entities(0, 0, 2, 'tail-batch')
        self.assertEqual({0, 1, 2, 3}, set(candidates))

    def test_inverse_functional_property_generates_alternative_heads(self):
        candidates = self.reasoner.negative_entities(0, 2, 2, 'head-batch')
        self.assertEqual({0, 1, 2, 3}, set(candidates))

    def test_irreflexive_property_generates_reflexive_corruptions(self):
        head_candidates = self.reasoner.negative_entities(0, 3, 1, 'head-batch')
        tail_candidates = self.reasoner.negative_entities(0, 3, 1, 'tail-batch')

        self.assertIn(1, set(head_candidates))
        self.assertIn(0, set(tail_candidates))

    @unittest.skipIf(TrainDataset is None, 'PyTorch is not installed')
    def test_train_dataset_filters_true_reasoner_candidates(self):
        np.random.seed(7)
        dataset = TrainDataset(
            self.triples, 4, 2, 16, 'tail-batch', 'reasoner', self.reasoner
        )

        _, negative_sample, _, _ = dataset[0]

        self.assertEqual(16, negative_sample.size(0))
        self.assertNotIn(2, set(negative_sample.tolist()))

    @unittest.skipIf(TrainDataset is None, 'PyTorch is not installed')
    def test_train_dataset_keeps_original_uniform_sampling(self):
        np.random.seed(7)
        log_file = tempfile.NamedTemporaryFile(delete=False)
        log_file.close()
        self.addCleanup(os.unlink, log_file.name)

        dataset = TrainDataset(
            self.triples,
            4,
            2,
            16,
            'tail-batch',
            'uniform',
            None,
            {idx: entity for entity, idx in self.entity2id.items()},
            {idx: relation for relation, idx in self.relation2id.items()},
            log_file.name,
            16,
        )

        _, negative_sample, _, _ = dataset[0]

        self.assertEqual(16, negative_sample.size(0))
        self.assertNotIn(2, set(negative_sample.tolist()))
        with open(log_file.name) as fin:
            self.assertTrue(all(
                line.split('\t')[1] == 'uniform'
                for line in fin
                if line.strip()
            ))

    def test_generate_ontology_creates_relation_labels(self):
        ontology = generate_ontology(
            ['worksFor'],
            [('alice', 'worksFor', 'acme'), ('bob', 'worksFor', 'otherOrg')],
            infer_functional_properties=True,
            infer_inverse_functional_properties=True,
            min_functional_support=2,
        )

        self.assertIn('rdfs:label "worksFor"', ontology)
        self.assertIn('owl:FunctionalProperty', ontology)
        self.assertIn('owl:InverseFunctionalProperty', ontology)

    def test_jena_materialized_reasoner_reads_tsv_cache(self):
        cache_dir = tempfile.TemporaryDirectory()
        self.addCleanup(cache_dir.cleanup)

        files = {
            'relation_domain.tsv': 'visits\thttp://example.org/Person\n',
            'relation_range.tsv': 'visits\thttp://example.org/Organization\n',
            'disjoint_classes.tsv': (
                'http://example.org/Person\t'
                'http://example.org/Organization\n'
            ),
            'functional_relations.tsv': '',
            'inverse_functional_relations.tsv': '',
            'irreflexive_relations.tsv': '',
            'entity_types.tsv': (
                'http://example.org/alice\thttp://example.org/Person\n'
                'http://example.org/bob\thttp://example.org/Person\n'
                'http://example.org/acme\thttp://example.org/Organization\n'
                'http://example.org/otherOrg\t'
                'http://example.org/Organization\n'
            ),
        }
        for filename, content in files.items():
            with open(os.path.join(cache_dir.name, filename), 'w') as fout:
                fout.write(content)

        reasoner = JenaMaterializedReasoner(
            cache_dir.name,
            self.triples,
            self.entity2id,
            {'visits': 1},
        )

        self.assertEqual({2, 3}, set(reasoner.negative_entities(
            0, 1, 2, 'head-batch'
        )))
        self.assertEqual({0, 1}, set(reasoner.negative_entities(
            0, 1, 2, 'tail-batch'
        )))


if __name__ == '__main__':
    unittest.main()
