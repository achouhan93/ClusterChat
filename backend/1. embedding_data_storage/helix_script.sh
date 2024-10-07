#!/bin/bash
#SBATCH --job-name=clustertalk-job
#SBATCH --partition=gpu-single
#SBATCH --ntasks=10
#SBATCH --time=100:00:00
#SBATCH --gres=gpu:2
#SBATCH --mem=30gb
#SBATCH --output=clustertalk-job.log
#SBATCH --error=clustertalk-job.err
#SBATCH --mail-user=chouhan@informatik.uni-heidelberg.de 
#SBATCH --mail-type=ALL

module load devel/miniconda/3
source $MINICONDA_HOME/etc/profile.d/conda.sh
conda activate cluster_talk_env

LOG_FILE="logs/insights_execution.log"

while true; do 
  LOG_LINE=$(grep "Processing for .* completed for the date" $LOG_FILE | tail -1); 
  DATE=$(echo "$LOG_LINE" | awk '{print $NF}'); 
  
  if [ "$DATE" = "1800-01-01" ]; then 
    echo "Exiting loop because date is 1800-01-01"; 
    break; 
  fi; 
  
  # Reduce the date by 1 day
  DATE_MINUS_ONE=$(date -d "$DATE - 1 day" +%Y-%m-%d)
  
  # Pass the reduced date to the Python script
  python3 main_sequential.py --vectorcreation "1800-01-01" "$DATE_MINUS_ONE" --chunking "sentence"; 
  
  sleep 10; 
done
