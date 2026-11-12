#!/bin/bash
#SBATCH --job-name=agentrun-diag
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --gres=gpu:1
#SBATCH --mem=4G
#SBATCH --time=00:05:00
#SBATCH --output=experiments/logs/diag-%j.out
#SBATCH --error=experiments/logs/diag-%j.err
echo "Start: $(date -Is)"; hostname; echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
nvidia-smi
free -h
lscpu | grep -E "^(Model name|CPU\(s\)|Socket)"
which python3; python3 --version
df -h $HOME /tmp | cat
ls $HOME/.cache/huggingface/hub | head -n 20
for u in https://huggingface.co https://pypi.org; do printf "%s -> " $u; curl -s -m 10 -o /dev/null -w "%{http_code}\n" $u || echo fail; done
echo "End: $(date -Is) exit=0"
