#!/usr/bin/env python3
import argparse
import json
import math
import shlex
import subprocess
import sys
import requests

# --- Constants & Heuristics ---

# Heuristic for estimating VRAM usage of weights.
# Most models are quantized. We'll use a simple mapping of:
# (approx_params_in_billions, quantization_type) -> bytes_per_param
# This is a rough approximation.
QUANTIZATION_BYTES = {
    "fp16": 2,
    "q8_0": 1,
    "q4_K_M": 0.6,  # Typical 4-bit quantization
    "q4_0": 0.5,
}

# Common model sizes (in billions of parameters)
MODEL_SIZE_HEURISTICS = {
    "gemma4:26b": 4,
    "bonsai-2:27b": 27,
    "qwen3.8:27b": 27
}

# Constants for KV Cache calculation (approximation for modern transformer architectures)
# A safer, conservative estimate of 1 MB per 1024 tokens for FP16.
BYTES_PER_TOKEN_FP16 = 1024  # 1 KB per token
BYTES_PER_TOKEN_Q8_0 = 512   # 0.5 KB per token

def get_model_info(model_name, ollama_url):
    """Queries Ollama API to get model details."""
    try:
        response = requests.get(f"{ollama_url}/api/tags")
        response.raise_for_status()
        models = response.json().get("models", [])
        for m in models:
            if m["name"].startswith(model_name):
                return m
        return None
    except Exception as e:
        print(f"Error querying Ollama API: {e}")
        return None

def estimate_weight_vram(model_name, ollama_url):
    """
    Estimates weight VRAM. 
    Tries to get it from Ollama API, otherwise uses heuristics.
    """
    info = get_model_info(model_name, ollama_url)
    if info and "size" in info:
        return info["size"]
    
    print(f"[*] Using heuristics for model: {model_name}")
    for pattern, params in MODEL_SIZE_HEURISTICS.items():
        if pattern in model_name:
            return params * 10**9 * QUANTIZATION_BYTES["q4_K_M"]
    
    print("[!] Unknown model size. Falling back to 7B Q4 estimate.")
    return 7 * 10**9 * QUANTIZATION_BYTES["q4_K_M"]

def calculate_max_context(available_vram_bytes, weight_vram_bytes, safety_margin_bytes):
    """Calculates max context for FP16 and Q8_0."""
    usable_vram = available_vram_bytes - weight_vram_bytes - safety_margin_bytes
    
    if usable_vram <= 0:
        return None, None

    # FP16
    max_ctx_fp16 = int(usable_vram / BYTES_PER_TOKEN_FP16)
    
    # Q8_0
    max_ctx_q8 = int(usable_vram / BYTES_PER_TOKEN_Q8_0)
    
    return max_ctx_fp16, max_ctx_q8

def create_model(model_name, modelfile_content, container_name="ia-ollama-1"):
    """Creates a new Ollama model by executing the ollama CLI inside the
    container, piping the Modelfile through stdin. The ollama CLI only
    exists inside the Ollama Docker image, not on the host, so we shell
    out to it via `docker exec`.
    """
    # Write the Modelfile to a temp file in the container, run `ollama create`,
    # then clean up. The Modelfile is carried on stdin (no shell quoting of its
    # contents); the model name is shell-quoted before interpolation.
    # We force OLLAMA_HOST=127.0.0.1 because the container sets
    # OLLAMA_HOST=0.0.0.0 (for the proxy to reach the server on all
    # interfaces), which is not a dialable address for the CLI's outbound
    # request to its own server.
    shell_cmd = (
        "cat > /tmp/modelfile.tmp && "
        "OLLAMA_HOST=127.0.0.1 ollama create {name} -f /tmp/modelfile.tmp && "
        "rm -f /tmp/modelfile.tmp"
    ).format(name=shlex.quote(model_name))
    cmd = ["docker", "exec", "-i", container_name, "sh", "-c", shell_cmd]
    try:
        process = subprocess.run(
            cmd,
            input=modelfile_content,
            text=True,
            capture_output=True,
            timeout=300
        )
        if process.returncode == 0:
            print(f"[+] Success! Model '{model_name}' created in '{container_name}'.")
        else:
            print(f"[!] Error creating model '{model_name}' (rc={process.returncode}):")
            print(process.stderr.rstrip())
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"[!] Error: docker exec timed out while creating model '{model_name}'.")
        sys.exit(1)
    except FileNotFoundError:
        print("[!] Error: 'docker' command not found on the host. Is Docker installed?")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Ollama Model Context Optimizer")
    parser.add_argument("--model", required=True, help="Base model name (e.g., gemma4:26b)")
    parser.add_argument("--target-vram", required=True, type=float, help="Target VRAM in GiB")
    parser.add_argument("--safety-margin", type=float, default=1.0, help="Safety margin in GiB")
    parser.add_argument("--ollama-url", default="http://localhost:8080", help="Ollama API URL")
    parser.add_argument("--container", default="ia-ollama-1", help="Ollama Docker container to exec into (default: ia-ollama-1)")
    parser.add_argument("--create", help="Name of the new optimized model to create")
    
    args = parser.parse_args()

    target_vram_bytes = args.target_vram * 1024**3
    safety_margin_bytes = args.safety_margin * 1024**3

    print(f"[*] Optimizing: {args.model}")
    print(f"[*] Target VRAM: {args.target_vram} GiB (with {args.safety_margin} GiB margin)")

    weight_vram = estimate_weight_vram(args.model, args.ollama_url)
    weight_vram_gib = weight_vram / 1024**3
    print(f"[*] Estimated weight VRAM: {weight_vram_gib:.2f} GiB")

    ctx_fp16, ctx_q8 = calculate_max_context(target_vram_bytes, weight_vram, safety_margin_bytes)

    if ctx_fp16 is None:
        print("[!] Error: Not enough VRAM for even minimal context.")
        sys.exit(1)

    print(f"[*] Results:")
    print(f"    - FP16 Max Context: {ctx_fp16} tokens")
    print(f"    - Q8_0 Max Context: {ctx_q8} tokens")

    # Recommend highest power-of-2 context that fits in FP16
    recommended_ctx = 2**math.floor(math.log2(ctx_fp16))
    recommended_ctx = (recommended_ctx // 1024) * 1024 # Round to nearest 1k
    if recommended_ctx < 1024: recommended_ctx = 1024

    modelfile_content = f"FROM {args.model}\nPARAMETER num_ctx {recommended_ctx}\n"
    
    print(f"[*] Recommended Modelfile content (for {recommended_ctx} tokens):")
    print("-" * 30)
    print(modelfile_content.strip())
    print("-" * 30)

    if args.create:
        print(f"[*] Creating model '{args.create}' in container '{args.container}'...")
        create_model(args.create, modelfile_content, args.container)

if __name__ == "__main__":
    main()
