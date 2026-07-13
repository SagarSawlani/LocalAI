# LocalAI File Manager

This repository hosts an AI-powered file manager capable of semantic document search, autonomous file organization, and natural language storage insights. The entire system is designed to run entirely locally on an Android device (OnePlus Nord 4) via Termux, leveraging local LLMs and embedding models for privacy and on-device execution.

## Project Structure

- `ai-file-manager/`: The main Python agent that plans and executes file operations using the local LLM.
- `backend/`: The API server that orchestrates commands between the frontend and the agent.
- `frontend/`: The user interface for interacting with the file manager.
- `commands.txt`: Reference for the `llama-server` startup commands.

## Technical Details: Local Models

The system relies on models quantized in GGUF format and served via `llama.cpp` (`llama-server`) on Termux to ensure efficient memory usage and fast generation on mobile hardware.

### 1. Main LLM (Qwen 1.5B)
Used by the AI agent to convert natural language queries into executable JSON commands (e.g., `move`, `scan`, `rename`, `insights`). 

- **Primary Model**: `qwen2.5-1.5b-instruct-q4_k_m.gguf`
  - **Size**: ~1.5 Billion parameters
  - **Quantization**: 4-bit (Q4_K_M)
  - **Context Window**: 4096 tokens
  - **Port**: `8080`
  - **Performance**: Extremely fast on-device generation with tight prompting constraints to enforce short paths and prevent hallucination.

**Command to start LLM:**
```bash
~/llama.cpp/build/bin/llama-server -m ~/models/qwen2.5-1.5b-instruct-q4_k_m.gguf -c 4096 --port 8080 --host 0.0.0.0
```

### 2. Embedding Model (Nomic Embed Text)
Used for the `locate_file` and `search_documents` capabilities. It computes dense vector representations of documents and queries to perform semantic search across the device's storage.

- **Model**: `nomic-embed-text-v1.5.Q4_K_M.gguf`
- **Type**: Text Embedding Model
- **Quantization**: 4-bit (Q4_K_M)
- **Context Window**: 8192 tokens (with RoPE scaling configured)
- **Port**: `8081`
- **Special Configurations**: Uses `yarn` RoPE scaling with a frequency scale of `.75` to accommodate larger document context limits during embedding generation.

**Command to start Embedding Model:**
```bash
~/llama.cpp/build/bin/llama-server -m ~/models/nomic-embed-text-v1.5.Q4_K_M.gguf --embedding --port 8081 --host 0.0.0.0 -c 8192 -b 8192 -ub 8192 --rope-scaling yarn --rope-freq-scale .75
```

## Running the Servers

The models and python environment are run natively on the phone using Termux. 
To ensure the OS does not kill the process during heavy inference, a wake lock is applied.

```bash
# Keep device awake
termux-wake-lock

# Activate virtual environment
source venv/bin/activate
```
