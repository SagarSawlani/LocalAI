# PocketMind

Offline AI assistant for Android (Termux): file management, document search, photo search, and voice — via natural language over HTTP.

---

## Quick Start

**Prerequisites:** Termux, `termux-setup-storage`, 8 GB+ RAM aarch64 phone (tested: OnePlus Nord 4)

**1. Build native deps**

```bash
cd ~ && git clone https://github.com/ggerganov/llama.cpp && cd llama.cpp && cmake -B build && cmake --build build -j$(nproc)
cd ~ && git clone https://github.com/ggerganov/whisper.cpp && cd whisper.cpp && cmake -B build && cmake --build build -j$(nproc)
cd ~ && git clone https://github.com/monatis/clip.cpp && cd clip.cpp && cmake -B build && cmake --build build -j$(nproc)
```

**2. Download models → `~/models/`**

| File | Used for |
|---|---|
| `qwen2.5-1.5b-instruct-q4_k_m.gguf` | Chat / intent / RAG |
| `nomic-embed-text-v1.5.Q4_K_M.gguf` | Document embeddings |
| `ggml-base-q5_1.bin` | Voice transcription |
| `clip-vit-b32-q5_1.gguf` | Photo search (in `~/clip.cpp/models/`) |

**3. Python setup**

```bash
cd ~/LocalAI/backend
python -m venv ~/venv && source ~/venv/bin/activate
pip install -r requirements.txt numpy pillow
```

**4. Start services** (3 terminals)

Chat LLM on port 8080:

```bash
termux-wake-lock
~/llama.cpp/build/bin/llama-server -m ~/models/qwen2.5-1.5b-instruct-q4_k_m.gguf -c 4096 -t 4 --port 8080 --host 0.0.0.0
```

Embeddings on port 8081:

```bash
~/llama.cpp/build/bin/llama-server -m ~/models/nomic-embed-text-v1.5.Q4_K_M.gguf --embedding --port 8081 --host 0.0.0.0 -c 8192 -b 8192 -ub 8192 --rope-scaling yarn --rope-freq-scale .75
```

FastAPI on port 8000:

```bash
source ~/venv/bin/activate && cd ~/LocalAI/backend && uvicorn main:app --host 0.0.0.0 --port 8000
```

**5. Index content** (first run)

```bash
source ~/venv/bin/activate
python ~/LocalAI/backend/document_search/run_index.py
python ~/LocalAI/ai-file-manager/tools/index_images.py
```

---

## Ports

| Port | Service |
|---|---|
| 8080 | llama-server — Qwen chat |
| 8081 | llama-server — nomic embeddings |
| 8000 | FastAPI — `/agent`, `/docs`, `/audio` |

---

## API Endpoints

| Method | Route | Purpose |
|---|---|---|
| POST | `/agent/execute` | Natural language → file/search action |
| POST | `/agent/execute-plan` | Run a confirmed plan |
| GET | `/docs/search?query=` | Vector search (no LLM) |
| GET | `/docs/ask?query=` | RAG answer |
| GET | `/docs/ask/stream?query=` | Streaming RAG |
| POST | `/docs/open?path=` | Open file via `termux-open` |
| POST | `/audio/transcribe` | Upload audio → transcript |

---

## Examples

One input → output per feature.

**File scan**

`POST /agent/execute` → `{"query": "list files in downloads"}`

→ `{"status": "executed", "tool": "scan", "result": [{"name": "report.pdf", "path": "/storage/emulated/0/Download/report.pdf", ...}]}`

**Move file** (needs confirm)

`{"query": "move Meeting Notes to documents"}` → `{"status": "needs_confirmation", "tool": "move", "plan": {...}}`

`{"query": "...", "auto_confirm": true}` → `{"status": "executed", "tool": "move", "result": {"status": "success", ...}}`

**Document Q&A**

`GET /docs/ask?query=what does my resume say about experience`

→ `{"answer": "...", "sources": [{"path": ".../resume.pdf", "score": 0.79}]}`

**Find file**

`POST /agent/execute` → `{"query": "find my resume"}`

→ `{"status": "executed", "tool": "locate_file", "result": {"results": [{"path": ".../resume.pdf", "score": 1.0}]}}`

**Photo search**

`{"query": "find a photo of a laptop"}`

→ `{"status": "executed", "tool": "photo_search", "result": [{"distance": 0.31, "path": ".../IMG_0042.jpg"}]}`

**Voice**

`POST /audio/transcribe` (upload `.m4a`)

→ `{"status": "success", "transcript": "find my resume"}`

---

## Confirmation

| Action | Behavior |
|---|---|
| scan, insights, locate, search, photo_search, find_duplicates | Runs immediately |
| move, rename | Returns `needs_confirmation` → resend with `auto_confirm: true` |
| delete | Same; CLI also requires typing `DELETE` |
| Ambiguous file | Returns `needs_choice` → resend with `choice_index` |

---

## Repo Layout

| Path | What |
|---|---|
| `ai-file-manager/agent/` | `llm.py`, `planner.py`, `executor.py`, `routes.py` |
| `ai-file-manager/tools/` | File ops, search, photo, transcribe |
| `backend/main.py` | FastAPI entry — mounts all routers |
| `backend/document_search/` | Indexing, RAG, audio routes |
| `backend/data/` | `doc_vectors.npy`, `doc_metadata.json`, `manifest.json` |

Flutter UI is a separate repo; connects over HTTP (Tailscale optional).

System design → [ARCHITECTURE.md](./ARCHITECTURE.md)
