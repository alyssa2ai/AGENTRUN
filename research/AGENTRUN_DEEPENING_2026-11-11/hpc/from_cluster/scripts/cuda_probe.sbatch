#!/bin/bash
#SBATCH --job-name=agentrun-cudaprobe
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --gres=gpu:1
#SBATCH --mem=8G
#SBATCH --time=00:05:00
#SBATCH --output=experiments/logs/cudaprobe-%j.out
#SBATCH --error=experiments/logs/cudaprobe-%j.err
# Read-only use of an existing environment, only to test whether CUDA initialises on the node.
echo "Start: $(date -Is) host=$(hostname) CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
cat /proc/driver/nvidia/version 2>&1 | head -n 2
ls /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.* 2>&1
PY=$HOME/cornea-work/cornea_nucleus/.venv_hpc/bin/python
$PY - <<PYEOF
import torch
print("torch", torch.__version__, "cuda build", torch.version.cuda)
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.device_count(), torch.cuda.get_device_name(0), round(torch.cuda.get_device_properties(0).total_memory/2**30,1), "GiB")
    x = torch.randn(4096, 4096, device="cuda"); print("matmul ok", float((x @ x).mean()))
PYEOF
echo "End: $(date -Is) exit=$?"
