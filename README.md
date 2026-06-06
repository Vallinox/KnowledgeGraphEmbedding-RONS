# Knowledge Graph Embedding with Jena-Guided Negative Sampling

This repository extends the original PyTorch implementation of
[RotatE: Knowledge Graph Embedding by Relational Rotation in Complex Space](https://openreview.net/forum?id=HkgEQnRqYQ).

The codebase is based on the original
[DeepGraphLearning/KnowledgeGraphEmbedding](https://github.com/DeepGraphLearning/KnowledgeGraphEmbedding)
repository.

The original training pipeline is preserved. The original uniform negative
sampler remains available and is still the default. This fork adds an optional
Apache Jena guided negative sampler that can be selected explicitly at training
time.

The only added training behavior is the optional generation of corrupted
triples guided by materialized RDF/OWL constraints.

## Features

Supported models:

[x] RotatE
[x] pRotatE
[x] TransE
[x] ComplEx
[x] DistMult

Evaluation:

[x] MRR, MR, HITS@1, HITS@3, HITS@10
[x] AUC-PR for Countries datasets

Negative sampling:

- Original uniform negative sampling, selected with `--negative_sampling uniform`
- Optional Jena guided negative sampling, selected with `--negative_sampling reasoner`
- RotatE self-adversarial negative weighting, enabled with `-adv`
- Optional logging and comparison of corrupted triples generated during training

Accelerators:

- CUDA with `--cuda`
- Apple Silicon GPU through PyTorch MPS with `--mps`
- CPU by omitting both `--cuda` and `--mps`

## Data Format

Each dataset directory must contain:

```text
- entities.dict: a dictionary map entities to unique ids
- relations.dict: a dictionary map relations to unique ids
- train.txt: the KGE model is trained to fit this data set
- valid.txt: create a blank file if no validation data is available
- test.txt: the KGE model is evaluated on this data set
```

The format follows the original RotatE repository:

```text
id<TAB>entity_name
id<TAB>relation_name
head<TAB>relation<TAB>tail
```

The repository uses these dataset directories:

```text
data/FB15k
data/FB15k-237
data/wn18
data/wn18rr
data/countries_S1
data/countries_S2
data/countries_S3
data/YAGO3-10
```

## Installation

Install Python dependencies:

```bash
pip install -r requirements.txt
```

The Jena materialization step requires Java and Maven. On macOS with Homebrew:

```bash
brew install openjdk maven
```

## Negative Sampling Modes

The sampler is selected with `--negative_sampling`.

Use the original RotatE behavior:

```bash
--negative_sampling uniform
```

This is the default, so omitting `--negative_sampling` keeps the original
negative sampling implementation.

Use the Jena guided sampler:

```bash
--negative_sampling reasoner \
--reasoner_cache_path data/wn18/jena_reasoner
```

When `--negative_sampling reasoner` is used, `--reasoner_cache_path` is required.
If the reasoner cache cannot provide enough corrupted candidates for a training
triple, the dataloader falls back to the original uniform sampler for that case.

## Ontology and Jena Materialization

The Jena guided sampler uses materialized RDF/OWL information based on:

- `rdfs:domain`
- `rdfs:range`
- `owl:disjointWith`
- `owl:AllDisjointClasses`
- `owl:complementOf`
- `owl:FunctionalProperty`
- `owl:InverseFunctionalProperty`
- `owl:IrreflexiveProperty`
- `rdfs:subClassOf`

The training loop does not run Java. Jena is used before training to create TSV
files, and PyTorch reads those TSV files during training.

Only entities are corrupted. The relation from the positive triple is kept
fixed for both the original sampler and the Jena guided sampler.

During training the sampler tries candidates in this order:

1. logical candidates from RDF/OWL constraints
2. original uniform sampling as fallback

For the Jena guided sampler, candidates are filtered against all known triples
from `train.txt`, `valid.txt`, and `test.txt` before being used. This reduces
known false negatives, although no method can fully rule out unknown true triples
under the open-world assumption.

Logical candidates from RDF/OWL constraints are sampled uniformly inside their
candidate set.

### Provide or Generate `ontology.ttl`

If you already have a verified ontology, place it in the dataset directory or
pass its path to `--ontology_path`.

For a heuristic ontology generated from the benchmark triples:

```bash
python codes/generate_ontology.py --data_path data/wn18
```

This writes:

```text
data/wn18/ontology.ttl
```

Important: the generated ontology is heuristic. It is useful for experiments,
but it should not be described as a verified domain ontology unless you review
and validate the axioms.

Functional properties are generated only if requested:

```bash
python codes/generate_ontology.py \
  --data_path data/wn18 \
  --infer_functional_properties
```

Inverse functional properties can also be inferred heuristically:

```bash
python codes/generate_ontology.py \
  --data_path data/wn18 \
  --infer_inverse_functional_properties
```

Both inference flags can be combined. Other axioms such as
`owl:IrreflexiveProperty`, `owl:AllDisjointClasses`, `owl:complementOf`, and
`rdfs:subClassOf` should usually come from a reviewed ontology.

### Materialize with Apache Jena

```bash
python codes/materialize_with_jena.py \
  --data_path data/wn18 \
  --ontology_path data/wn18/ontology.ttl \
  --output_path data/wn18/jena_reasoner
```

The output directory contains:

```text
entity_types.tsv
relation_domain.tsv
relation_range.tsv
disjoint_classes.tsv
functional_relations.tsv
inverse_functional_relations.tsv
irreflexive_relations.tsv
```

These files are the reasoner cache passed to training with
`--reasoner_cache_path`.

## Training Examples

### Original RotatE Baseline on WN18

This uses the original uniform negative sampler:

```bash
python -u codes/run.py \
  --do_train --do_valid --do_test \
  --mps \
  --data_path data/wn18 \
  --model RotatE \
  --negative_sampling uniform \
  -b 512 -n 1024 -d 500 -g 12.0 \
  -a 0.5 -adv \
  -lr 0.0001 \
  --max_steps 80000 \
  --test_batch_size 8 \
  -save models/RotatE_wn18_uniform \
  -cpu 0 \
  -de
```

### Jena Guided RotatE on WN18

First create the Jena cache:

```bash
python codes/generate_ontology.py --data_path data/wn18
python codes/materialize_with_jena.py \
  --data_path data/wn18 \
  --ontology_path data/wn18/ontology.ttl \
  --output_path data/wn18/jena_reasoner
```

Then train with the reasoner sampler:

```bash
python -u codes/run.py \
  --do_train --do_valid --do_test \
  --mps \
  --data_path data/wn18 \
  --model RotatE \
  --negative_sampling reasoner \
  --reasoner_cache_path data/wn18/jena_reasoner \
  -b 512 -n 1024 -d 500 -g 12.0 \
  -a 0.5 -adv \
  -lr 0.0001 \
  --max_steps 80000 \
  --test_batch_size 8 \
  -save models/RotatE_wn18_jena \
  -cpu 0 \
  -de
```

### Jena Guided RotatE on Countries S1

```bash
python codes/generate_ontology.py --data_path data/countries_S1
python codes/materialize_with_jena.py \
  --data_path data/countries_S1 \
  --ontology_path data/countries_S1/ontology.ttl \
  --output_path data/countries_S1/jena_reasoner
```

```bash
python -u codes/run.py \
  --do_train --do_valid --do_test \
  --mps \
  --countries \
  --data_path data/countries_S1 \
  --model RotatE \
  --negative_sampling reasoner \
  --reasoner_cache_path data/countries_S1/jena_reasoner \
  -b 512 -n 64 -d 1000 -g 0.1 \
  -a 1.0 -adv \
  -lr 0.000002 \
  --max_steps 40000 \
  --test_batch_size 8 \
  -save models/RotatE_countries_S1_jena \
  -cpu 0 \
  -de
```

For CUDA, replace `--mps` with `--cuda`. For CPU, remove `--mps`.

## Logging and Comparing Corrupted Triples

To inspect the corrupted triples used during training, pass:

```bash
--negative_sample_log_path logs/RotatE_wn18_jena_negatives.tsv \
--negative_sample_log_limit 10000
```

The log contains the positive triple, the corrupted triple, the batch mode, and
the source used to generate the negative sample.

The `source` column can contain:

```text
uniform
reasoner
reasoner_fallback_uniform
```

The logged corrupted relation is always the same relation as the positive
triple. For `head-batch` only the head is replaced; for `tail-batch` only the
tail is replaced.

Summarize one log:

```bash
python codes/negative_sample_log.py summarize \
  --log_path logs/RotatE_wn18_jena_negatives.tsv \
  --limit 50
```

Compare the original sampler against the Jena guided sampler:

```bash
python codes/negative_sample_log.py compare \
  --left_log logs/RotatE_wn18_uniform_negatives.tsv \
  --right_log logs/RotatE_wn18_jena_negatives.tsv \
  --left_name uniform \
  --right_name jena \
  --limit 50
```

## Best Configurations

The original best configurations are still listed in:

```text
best_config.sh
```

At the end of the file there is an additional section for all RotatE datasets.
For each dataset the order is:

1. generate `ontology.ttl`
2. materialize the Jena cache
3. train RotatE with `--negative_sampling reasoner`
4. train the original baseline with `--negative_sampling uniform`
5. compare the logged corrupted triples

The commands in that section are explicit shell commands, so you can copy only
the block for the dataset you want to run.

Example original command style:

```bash
bash run.sh train RotatE wn18 0 0 512 1024 500 12.0 0.5 0.0001 80000 8 -de
```

The original `run.sh` uses CUDA. On macOS, use the direct `codes/run.py`
commands with `--mps`.

## Apple Silicon Notes

Check MPS availability:

```bash
python - <<'PY'
import torch
print(torch.backends.mps.is_built())
print(torch.backends.mps.is_available())
PY
```

If both values are `True`, you can train with `--mps`. If MPS is unavailable,
remove `--mps` and run on CPU.

## Implementation Notes

The original sampler is still implemented in `codes/dataloader.py` and selected
with `--negative_sampling uniform`.

The Jena guided sampler is implemented through:

- `codes/reasoner.py`
- `codes/generate_ontology.py`
- `codes/materialize_with_jena.py`
- `jena-materializer/`

The command-line selection is handled in `codes/run.py`.

## Citation

Original source code:
[DeepGraphLearning/KnowledgeGraphEmbedding](https://github.com/DeepGraphLearning/KnowledgeGraphEmbedding).

If you use the original RotatE implementation or models, cite:

```bibtex
@inproceedings{
  sun2018rotate,
  title={RotatE: Knowledge Graph Embedding by Relational Rotation in Complex Space},
  author={Zhiqing Sun and Zhi-Hong Deng and Jian-Yun Nie and Jian Tang},
  booktitle={International Conference on Learning Representations},
  year={2019},
  url={https://openreview.net/forum?id=HkgEQnRqYQ}
}
```
