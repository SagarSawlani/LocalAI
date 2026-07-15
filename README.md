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

## How It Works (Under the Hood)

PocketMind routes your requests through different local models and scripts depending on what you ask.

### 1. AI Assistant Mode (File Management)
When you ask the assistant to manage your files (e.g., "Find my resume and move it to Documents"), the flow is:
1. **Flutter App** sends the text query to the **FastAPI Backend** (`/agent/execute`).
2. **LLM Planner (`planner.py`)**: The backend forwards your request to the local **Qwen 2.5 (1.5B)** model running on port 8080.
3. **Intent Parsing**: Qwen analyzes your text and selects the appropriate Python tool from `tools/` (e.g., `scan`, `move`, `locate_file`, `photo_search`).
4. **Execution (`executor.py`)**: The backend runs the chosen Python tool on your phone's file system.
5. **Confirmation**: If the tool is destructive (like `move` or `delete`), the backend pauses and sends a "Plan" back to Flutter asking for your approval.
6. **Result**: Once executed, the result is sent back to Flutter and displayed as a chat bubble or file card.

### 2. Search Phone Mode (Document Q&A / RAG)
When you switch to "Search Phone" and ask a question (e.g., "What does my syllabus say about machine learning?"):
1. **Embedding (`embedder.py`)**: The backend sends your query to the **Nomic Embed Text** model running on port 8081, which converts your question into a mathematical vector.
2. **Vector Search (`vector_store.py`)**: FAISS (a local vector database) compares your query vector against all your indexed PDFs and documents to find the top 5 most relevant paragraphs.
3. **Context Generation (`qa.py`)**: The retrieved paragraphs (along with their file paths) are combined into a prompt.
4. **LLM Answering**: This massive prompt is sent to the **Qwen 2.5 (1.5B)** model, asking it to answer your question using *only* the provided paragraphs.
5. **Streaming**: Qwen streams the answer token-by-token back to the Flutter app in real-time, appending the source file cards at the very end.

---

## Action Flow Examples

Here is exactly what happens when you run specific commands:

**Example 1: "Find a photo of a laptop"**
* **Model Used:** CLIP (ViT-B/32)
* **Tool Called:** `photo_search`
* **What Happens:** The text "a laptop" is embedded by the local CLIP model into a vector. FAISS compares this text vector against the pre-computed vectors of all your photos in the DCIM folder. It returns the file paths of the closest visual matches to Flutter.

**Example 2: "Rename DS question bank PT2 to DS_QB"**
* **Model Used:** Qwen 2.5 (1.5B)
* **Tool Called:** `rename`
* **What Happens:** Qwen extracts the source and target filenames. `planner.py` tries to resolve "DS question bank PT2" to an exact file path. Since you didn't provide an extension, it falls back to a keyword search (`locate_file`) to find the exact PDF. It then returns a plan asking for your confirmation before executing the OS `os.rename()` command.

**Example 3: "Scan my downloads folder"**
* **Model Used:** Qwen 2.5 (1.5B)
* **Tool Called:** `scan`
* **What Happens:** Qwen detects the intent to list files and extracts the directory name "downloads". `planner.py` resolves "downloads" to `/storage/emulated/0/Download`. The `scan.py` tool runs an `os.scandir()`, pulling file sizes, types, and modified dates, and returns the list to Flutter to render as file cards.

---

## Confirmation Rules

For safety, the `executor.py` enforces strict confirmation rules before touching your files:

| Tool | Requires User Approval? |
|---|---|
| `scan`, `insights`, `locate_file`, `photo_search`, `find_duplicates` | **No** (Runs immediately) |
| `move`, `rename` | **Yes** (Requires tapping "Confirm" in Flutter) |
| `delete` | **Yes** (Requires manual confirmation to prevent accidental data loss) |

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
