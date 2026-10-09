# Code Availability Statement

Training scripts, serving scripts for the V1, E4, and V2 conditions, and
the evaluation harness are released at
https://github.com/Alyssa-286/AGENTRUN.

File map:

- `eval/tasks.py`              -- 23-task benchmark
- `eval/harness.py`            -- scoring logic
- `training/colab_train_7b.py` -- V1 training
- `training/colab_train_7b_v2.py` -- V2 training
- `serving/colab_server.py`    -- V1 parser + server
- `serving/colab_server_e4.py` -- V2 parser + V1 adapter (E4)
- `serving/colab_server_v2.py` -- V2 parser + V2 adapter
- `results/`                   -- raw per-condition result files
