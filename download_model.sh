#!/bin/bash

echo "Downloading Qwen 2.5 3B Instruct (Q4_K_M)"
mkdir -p models

wget -O models/qwen2.5-3b-instruct-q4_K_M.gguf \
  https://huggingface.co/bartowski/Qwen2.5-3B-Instruct-GGUF/resolve/main/Qwen2.5-3B-Instruct-Q4_K_M.gguf

echo "Model downloaded to models/qwen2.5-3b-instruct-q4_K_M.gguf"
ls -lh models/