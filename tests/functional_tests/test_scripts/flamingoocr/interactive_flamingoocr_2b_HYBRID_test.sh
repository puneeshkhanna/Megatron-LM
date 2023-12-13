#! /bin/bash

# These paths should be modified by user to use their source code and output dir
CHECKPOINT_PATH=/lustre/fsw/adlr/adlr-nlp/jbarker/next-llm/output/flamingoocr_2b_HYBRID_test/checkpoints
TENSORBOARD_DIR=/lustre/fsw/adlr/adlr-nlp/jbarker/next-llm/output/flamingoocr_2b_HYBRID_test/tensorboard_logs
SCRIPTS_DIR=/lustre/fsw/adlr/adlr-nlp/jbarker/next-llm/source/megatron-lm

DATA_PATH=/lustre/fsw/adlr/adlr-nlp/adlr_ci/megatron/data/flamingo_data
mkdir /workspace/data
ln -s $DATA_PATH /workspace/data/flamingo_data

USE_CORE=0
USE_TE=0
MBS=4
GBS=32
MAX_STEPS=50
NUM_NODES=1
TP_SIZE=1
PP_SIZE=1
export ADDITIONAL_PARAMS="--load /lustre/fsw/adlr/adlr-nlp/adlr_ci/megatron/data/flamingo_data/gpt3-2b-multi-1.1t-gtc --use-hybrid-visual-backbones --xattn-sam-num 1 --xattn-clip-num 3 --visual-arch HybridSAMCLIP --visual-arch-clip L_14 --visual-type-clip vit --visual-path-clip /lustre/fsw/adlr/adlr-nlp/adlr_ci/megatron/data/flamingo_data/vit_L_14_336px --img-h-clip 336 --img-w-clip 336 --visual-arch-sam SAM_L --visual-type-sam sam --visual-path-sam /lustre/fsw/adlr/adlr-nlp/adlr_ci/megatron/data/flamingo_data/SAM_L_16 --img-h-sam 1024 --img-w-sam 1024 --img-h 1024 --img-w 1024 --SAM-randinit"

bash ./tests/functional_tests/test_scripts/flamingoocr/finetune_flamingoocr_distributed_test.sh DATA_PATH=$DATA_PATH CHECKPOINT_PATH=$CHECKPOINT_PATH TENSORBOARD_DIR=$TENSORBOARD_DIR SCRIPTS_DIR=$SCRIPTS_DIR USE_TE=$USE_TE TP_SIZE=$TP_SIZE PP_SIZE=$PP_SIZE VP_SIZE=$VP_SIZE NUM_NODES=$NUM_NODES MAX_STEPS=$MAX_STEPS USE_CORE=$USE_CORE MBS=$MBS GBS=$GBS

python tests/functional_tests/python_test_utils/get_test_results_from_tensorboard_logs.py /lustre/fsw/adlr/adlr-nlp/jbarker/next-llm/output/flamingoocr_2b_HYBRID_test/tensorboard_logs flamingoocr_2b_HYBRID_test

export EXPECTED_METRICS_FILE=tests/functional_tests/test_results/flamingoocr/flamingoocr_2b_HYBRID_test.json

export LOGS_DIR=/lustre/fsw/adlr/adlr-nlp/jbarker/next-llm/output/flamingoocr_2b_HYBRID_test/tensorboard_logs

pytest tests/functional_tests/python_test_utils/test_ci_pipeline.py