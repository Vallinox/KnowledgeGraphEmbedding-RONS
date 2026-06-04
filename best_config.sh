# Best Configuration for RotatE
#
bash run.sh train RotatE FB15k 0 0 1024 256 1000 24.0 1.0 0.0001 150000 16 -de
bash run.sh train RotatE FB15k-237 0 0 1024 256 1000 9.0 1.0 0.00005 100000 16 -de
bash run.sh train RotatE wn18 0 0 512 1024 500 12.0 0.5 0.0001 80000 8 -de
bash run.sh train RotatE wn18rr 0 0 512 1024 500 6.0 0.5 0.00005 80000 8 -de
bash run.sh train RotatE countries_S1 0 0 512 64 1000 0.1 1.0 0.000002 40000 8 -de --countries
bash run.sh train RotatE countries_S2 0 0 512 64 1000 0.1 1.0 0.000002 40000 8 -de --countries 
bash run.sh train RotatE countries_S3 0 0 512 64 1000 0.1 1.0 0.000002 40000 8 -de --countries
bash run.sh train RotatE YAGO3-10 0 0 1024 400 500 24.0 1.0 0.0002 100000 4 -de
#
# Best Configuration for pRotatE
#
bash run.sh train pRotatE FB15k 0 0 1024 256 1000 24.0 1.0 0.0001 150000 16
bash run.sh train pRotatE FB15k-237 0 0 1024 256 1000 9.0 1.0 0.00005 100000 16
bash run.sh train pRotatE wn18 0 0 512 1024 500 12.0 0.5 0.0001 80000 8
bash run.sh train pRotatE wn18rr 0 0 512 1024 500 6.0 0.5 0.00005 80000 8
bash run.sh train pRotatE countries_S1 0 0 512 64 1000 0.1 1.0 0.000002 40000 8 --countries
bash run.sh train pRotatE countries_S2 0 0 512 64 1000 0.1 1.0 0.000002 40000 8 --countries
bash run.sh train pRotatE countries_S3 0 0 512 64 1000 0.1 1.0 0.000002 40000 8 --countries
#
# Best Configuration for TransE
# 
bash run.sh train TransE FB15k 0 0 1024 256 1000 24.0 1.0 0.0001 150000 16
bash run.sh train TransE FB15k-237 0 0 1024 256 1000 9.0 1.0 0.00005 100000 16
bash run.sh train TransE wn18 0 0 512 1024 500 12.0 0.5 0.0001 80000 8
bash run.sh train TransE wn18rr 0 0 512 1024 500 6.0 0.5 0.00005 80000 8
bash run.sh train TransE countries_S1 0 0 512 64 1000 0.1 1.0 0.000002 40000 8 --countries
bash run.sh train TransE countries_S2 0 0 512 64 1000 0.1 1.0 0.000002 40000 8 --countries
bash run.sh train TransE countries_S3 0 0 512 64 1000 0.1 1.0 0.000002 40000 8 --countries
#
# Best Configuration for ComplEx
# 
bash run.sh train ComplEx FB15k 0 0 1024 256 1000 500.0 1.0 0.001 150000 16 -de -dr -r 0.000002
bash run.sh train ComplEx FB15k-237 0 0 1024 256 1000 200.0 1.0 0.001 100000 16 -de -dr -r 0.00001
bash run.sh train ComplEx wn18 0 0 512 1024 500 200.0 1.0 0.001 80000 8 -de -dr -r 0.00001
bash run.sh train ComplEx wn18rr 0 0 512 1024 500 200.0 1.0 0.002 80000 8 -de -dr -r 0.000005
bash run.sh train ComplEx countries_S1 0 0 512 64 1000 1.0 1.0 0.000002 40000 8 -de -dr -r 0.0005 --countries
bash run.sh train ComplEx countries_S2 0 0 512 64 1000 1.0 1.0 0.000002 40000 8 -de -dr -r 0.0005 --countries
bash run.sh train ComplEx countries_S3 0 0 512 64 1000 1.0 1.0 0.000002 40000 8 -de -dr -r 0.0005 --countries
#
# Best Configuration for DistMult
# 
bash run.sh train DistMult FB15k 0 0 1024 256 2000 500.0 1.0 0.001 150000 16 -r 0.000002
bash run.sh train DistMult FB15k-237 0 0 1024 256 2000 200.0 1.0 0.001 100000 16 -r 0.00001
bash run.sh train DistMult wn18 0 0 512 1024 1000 200.0 1.0 0.001 80000 8 -r 0.00001
bash run.sh train DistMult wn18rr 0 0 512 1024 1000 200.0 1.0 0.002 80000 8 -r 0.000005
bash run.sh train DistMult countries_S1 0 0 512 64 2000 1.0 1.0 0.000002 40000 8 -r 0.0005 --countries
bash run.sh train DistMult countries_S2 0 0 512 64 2000 1.0 1.0 0.000002 40000 8 -r 0.0005 --countries
bash run.sh train DistMult countries_S3 0 0 512 64 2000 1.0 1.0 0.000002 40000 8 -r 0.0005 --countries
#

# RotatE with Apache Jena-guided negative sampling
#
# For each RotatE dataset below the Jena-guided run is executed first, followed
# by the original uniform negative sampler baseline with the same hyper-parameters.
# The final command compares the corrupted triples logged by the two samplers.
#
# On macOS use --mps. On CPU remove --mps. On CUDA replace --mps with --cuda.
#

mkdir -p logs

# FB15k: RotatE with Jena-guided negative sampling
python codes/generate_ontology.py --data_path data/FB15k
python codes/materialize_with_jena.py --data_path data/FB15k --ontology_path data/FB15k/ontology.ttl --output_path data/FB15k/jena_reasoner
python -u codes/run.py --do_train --do_valid --do_test --mps --data_path data/FB15k --model RotatE --negative_sampling reasoner --reasoner_cache_path data/FB15k/jena_reasoner -b 1024 -n 256 -d 1000 -g 24.0 -a 1.0 -adv -lr 0.0001 --max_steps 150000 --test_batch_size 16 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_FB15k_jena -cpu 0 -de --negative_sample_log_path logs/RotatE_FB15k_jena_negatives.tsv --negative_sample_log_limit 10000
# FB15k: original RotatE baseline with logged corrupted triples
python -u codes/run.py --do_train --do_valid --do_test --mps --data_path data/FB15k --model RotatE --negative_sampling uniform -b 1024 -n 256 -d 1000 -g 24.0 -a 1.0 -adv -lr 0.0001 --max_steps 150000 --test_batch_size 16 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_FB15k_uniform -cpu 0 -de --negative_sample_log_path logs/RotatE_FB15k_uniform_negatives.tsv --negative_sample_log_limit 10000
python codes/negative_sample_log.py compare --left_log logs/RotatE_FB15k_uniform_negatives.tsv --right_log logs/RotatE_FB15k_jena_negatives.tsv --left_name uniform --right_name jena --limit 50

# FB15k-237: RotatE with Jena-guided negative sampling
python codes/generate_ontology.py --data_path data/FB15k-237
python codes/materialize_with_jena.py --data_path data/FB15k-237 --ontology_path data/FB15k-237/ontology.ttl --output_path data/FB15k-237/jena_reasoner
python -u codes/run.py --do_train --do_valid --do_test --mps --data_path data/FB15k-237 --model RotatE --negative_sampling reasoner --reasoner_cache_path data/FB15k-237/jena_reasoner -b 1024 -n 256 -d 1000 -g 9.0 -a 1.0 -adv -lr 0.00005 --max_steps 100000 --test_batch_size 16 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_FB15k-237_jena -cpu 0 -de --negative_sample_log_path logs/RotatE_FB15k-237_jena_negatives.tsv --negative_sample_log_limit 10000
# FB15k-237: original RotatE baseline with logged corrupted triples
python -u codes/run.py --do_train --do_valid --do_test --mps --data_path data/FB15k-237 --model RotatE --negative_sampling uniform -b 1024 -n 256 -d 1000 -g 9.0 -a 1.0 -adv -lr 0.00005 --max_steps 100000 --test_batch_size 16 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_FB15k-237_uniform -cpu 0 -de --negative_sample_log_path logs/RotatE_FB15k-237_uniform_negatives.tsv --negative_sample_log_limit 10000
python codes/negative_sample_log.py compare --left_log logs/RotatE_FB15k-237_uniform_negatives.tsv --right_log logs/RotatE_FB15k-237_jena_negatives.tsv --left_name uniform --right_name jena --limit 50

# WN18: RotatE with Jena-guided negative sampling
python codes/generate_ontology.py --data_path data/wn18
python codes/materialize_with_jena.py --data_path data/wn18 --ontology_path data/wn18/ontology.ttl --output_path data/wn18/jena_reasoner
python -u codes/run.py --do_train --do_valid --do_test --mps --data_path data/wn18 --model RotatE --negative_sampling reasoner --reasoner_cache_path data/wn18/jena_reasoner -b 512 -n 1024 -d 500 -g 12.0 -a 0.5 -adv -lr 0.0001 --max_steps 80000 --test_batch_size 8 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_wn18_jena -cpu 0 -de --negative_sample_log_path logs/RotatE_wn18_jena_negatives.tsv --negative_sample_log_limit 10000
# WN18: original RotatE baseline with logged corrupted triples
python -u codes/run.py --do_train --do_valid --do_test --mps --data_path data/wn18 --model RotatE --negative_sampling uniform -b 512 -n 1024 -d 500 -g 12.0 -a 0.5 -adv -lr 0.0001 --max_steps 80000 --test_batch_size 8 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_wn18_uniform -cpu 0 -de --negative_sample_log_path logs/RotatE_wn18_uniform_negatives.tsv --negative_sample_log_limit 10000
python codes/negative_sample_log.py compare --left_log logs/RotatE_wn18_uniform_negatives.tsv --right_log logs/RotatE_wn18_jena_negatives.tsv --left_name uniform --right_name jena --limit 50

# WN18RR: RotatE with Jena-guided negative sampling
python codes/generate_ontology.py --data_path data/wn18rr
python codes/materialize_with_jena.py --data_path data/wn18rr --ontology_path data/wn18rr/ontology.ttl --output_path data/wn18rr/jena_reasoner
python -u codes/run.py --do_train --do_valid --do_test --mps --data_path data/wn18rr --model RotatE --negative_sampling reasoner --reasoner_cache_path data/wn18rr/jena_reasoner -b 512 -n 1024 -d 500 -g 6.0 -a 0.5 -adv -lr 0.00005 --max_steps 80000 --test_batch_size 8 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_wn18rr_jena -cpu 0 -de --negative_sample_log_path logs/RotatE_wn18rr_jena_negatives.tsv --negative_sample_log_limit 10000
# WN18RR: original RotatE baseline with logged corrupted triples
python -u codes/run.py --do_train --do_valid --do_test --mps --data_path data/wn18rr --model RotatE --negative_sampling uniform -b 512 -n 1024 -d 500 -g 6.0 -a 0.5 -adv -lr 0.00005 --max_steps 80000 --test_batch_size 8 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_wn18rr_uniform -cpu 0 -de --negative_sample_log_path logs/RotatE_wn18rr_uniform_negatives.tsv --negative_sample_log_limit 10000
python codes/negative_sample_log.py compare --left_log logs/RotatE_wn18rr_uniform_negatives.tsv --right_log logs/RotatE_wn18rr_jena_negatives.tsv --left_name uniform --right_name jena --limit 50

# Countries S1: RotatE with Jena-guided negative sampling
python codes/generate_ontology.py --data_path data/countries_S1
python codes/materialize_with_jena.py --data_path data/countries_S1 --ontology_path data/countries_S1/ontology.ttl --output_path data/countries_S1/jena_reasoner
python -u codes/run.py --do_train --do_valid --do_test --mps --countries --data_path data/countries_S1 --model RotatE --negative_sampling reasoner --reasoner_cache_path data/countries_S1/jena_reasoner -b 512 -n 64 -d 1000 -g 0.1 -a 1.0 -adv -lr 0.000002 --max_steps 40000 --test_batch_size 8 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_countries_S1_jena -cpu 0 -de --negative_sample_log_path logs/RotatE_countries_S1_jena_negatives.tsv --negative_sample_log_limit 10000
# Countries S1: original RotatE baseline with logged corrupted triples
python -u codes/run.py --do_train --do_valid --do_test --mps --countries --data_path data/countries_S1 --model RotatE --negative_sampling uniform -b 512 -n 64 -d 1000 -g 0.1 -a 1.0 -adv -lr 0.000002 --max_steps 40000 --test_batch_size 8 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_countries_S1_uniform -cpu 0 -de --negative_sample_log_path logs/RotatE_countries_S1_uniform_negatives.tsv --negative_sample_log_limit 10000
python codes/negative_sample_log.py compare --left_log logs/RotatE_countries_S1_uniform_negatives.tsv --right_log logs/RotatE_countries_S1_jena_negatives.tsv --left_name uniform --right_name jena --limit 50

# Countries S2: RotatE with Jena-guided negative sampling
python codes/generate_ontology.py --data_path data/countries_S2
python codes/materialize_with_jena.py --data_path data/countries_S2 --ontology_path data/countries_S2/ontology.ttl --output_path data/countries_S2/jena_reasoner
python -u codes/run.py --do_train --do_valid --do_test --mps --countries --data_path data/countries_S2 --model RotatE --negative_sampling reasoner --reasoner_cache_path data/countries_S2/jena_reasoner -b 512 -n 64 -d 1000 -g 0.1 -a 1.0 -adv -lr 0.000002 --max_steps 40000 --test_batch_size 8 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_countries_S2_jena -cpu 0 -de --negative_sample_log_path logs/RotatE_countries_S2_jena_negatives.tsv --negative_sample_log_limit 10000
# Countries S2: original RotatE baseline with logged corrupted triples
python -u codes/run.py --do_train --do_valid --do_test --mps --countries --data_path data/countries_S2 --model RotatE --negative_sampling uniform -b 512 -n 64 -d 1000 -g 0.1 -a 1.0 -adv -lr 0.000002 --max_steps 40000 --test_batch_size 8 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_countries_S2_uniform -cpu 0 -de --negative_sample_log_path logs/RotatE_countries_S2_uniform_negatives.tsv --negative_sample_log_limit 10000
python codes/negative_sample_log.py compare --left_log logs/RotatE_countries_S2_uniform_negatives.tsv --right_log logs/RotatE_countries_S2_jena_negatives.tsv --left_name uniform --right_name jena --limit 50

# Countries S3: RotatE with Jena-guided negative sampling
python codes/generate_ontology.py --data_path data/countries_S3
python codes/materialize_with_jena.py --data_path data/countries_S3 --ontology_path data/countries_S3/ontology.ttl --output_path data/countries_S3/jena_reasoner
python -u codes/run.py --do_train --do_valid --do_test --mps --countries --data_path data/countries_S3 --model RotatE --negative_sampling reasoner --reasoner_cache_path data/countries_S3/jena_reasoner -b 512 -n 64 -d 1000 -g 0.1 -a 1.0 -adv -lr 0.000002 --max_steps 40000 --test_batch_size 8 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_countries_S3_jena -cpu 0 -de --negative_sample_log_path logs/RotatE_countries_S3_jena_negatives.tsv --negative_sample_log_limit 10000
# Countries S3: original RotatE baseline with logged corrupted triples
python -u codes/run.py --do_train --do_valid --do_test --mps --countries --data_path data/countries_S3 --model RotatE --negative_sampling uniform -b 512 -n 64 -d 1000 -g 0.1 -a 1.0 -adv -lr 0.000002 --max_steps 40000 --test_batch_size 8 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_countries_S3_uniform -cpu 0 -de --negative_sample_log_path logs/RotatE_countries_S3_uniform_negatives.tsv --negative_sample_log_limit 10000
python codes/negative_sample_log.py compare --left_log logs/RotatE_countries_S3_uniform_negatives.tsv --right_log logs/RotatE_countries_S3_jena_negatives.tsv --left_name uniform --right_name jena --limit 50

# YAGO3-10: RotatE with Jena-guided negative sampling
python codes/generate_ontology.py --data_path data/YAGO3-10
python codes/materialize_with_jena.py --data_path data/YAGO3-10 --ontology_path data/YAGO3-10/ontology.ttl --output_path data/YAGO3-10/jena_reasoner
python -u codes/run.py --do_train --do_valid --do_test --mps --data_path data/YAGO3-10 --model RotatE --negative_sampling reasoner --reasoner_cache_path data/YAGO3-10/jena_reasoner -b 1024 -n 400 -d 500 -g 24.0 -a 1.0 -adv -lr 0.0002 --max_steps 100000 --test_batch_size 4 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_YAGO3-10_jena -cpu 0 -de --negative_sample_log_path logs/RotatE_YAGO3-10_jena_negatives.tsv --negative_sample_log_limit 10000
# YAGO3-10: original RotatE baseline with logged corrupted triples
python -u codes/run.py --do_train --do_valid --do_test --mps --data_path data/YAGO3-10 --model RotatE --negative_sampling uniform -b 1024 -n 400 -d 500 -g 24.0 -a 1.0 -adv -lr 0.0002 --max_steps 100000 --test_batch_size 4 --save_checkpoint_steps 10000 --valid_steps 10000 --log_steps 100 --test_log_steps 1000 -save models/RotatE_YAGO3-10_uniform -cpu 0 -de --negative_sample_log_path logs/RotatE_YAGO3-10_uniform_negatives.tsv --negative_sample_log_limit 10000
python codes/negative_sample_log.py compare --left_log logs/RotatE_YAGO3-10_uniform_negatives.tsv --right_log logs/RotatE_YAGO3-10_jena_negatives.tsv --left_name uniform --right_name jena --limit 50
