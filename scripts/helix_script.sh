#!/bin/bash
#SBATCH --job-name=clustertalk-job
#SBATCH --partition=single
#SBATCH --ntasks=10
#SBATCH --time=48:00:00
#SBATCH --gres=gpu:3
#SBATCH --mem=50gb
#SBATCH --output=clustertalk-job.log
#SBATCH --error=clustertalk-job.err
#SBATCH --mail-user=chouhan@informatik.uni-heidelberg.de 
#SBATCH --mail-type=ALL

module load devel/miniconda/3
source $MINICONDA_HOME/etc/profile.d/conda.sh
conda activate cluster_talk_env

cd ./backend/1. embedding_data_storage
python3 main.py --vectorcreation "1800-01-01" "2024-08-01" --chunking "complete"