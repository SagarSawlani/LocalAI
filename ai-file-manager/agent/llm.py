import requests
import json

LLAMA_SERVER_URL = "http://localhost:8080/v1/chat/completions"

SYSTEM_PROMPT = """You are a file management assistant. Convert the user's natural language request into a JSON command.

IMPORTANT: For "src", "dest", and "path" fields, use ONLY the short name the user mentioned (e.g. "Hackathon Brochure", "downloads", "DCIM"). Do NOT invent or guess full absolute paths. The system will resolve the actual paths automatically.

Available tools:
- "move": move a file/folder. Requires "src" (just the filename the user mentioned) and "dest" (just the folder name the user mentioned, e.g. "downloads", "documents").
- "scan": list contents of a directory. Requires "path" (just the folder name).
- "rename": rename a file/folder in place. Requires "src" (just the current filename) and "new_name" (just the new filename).
- "insights": show a storage breakdown (categories, sizes, largest files) of a directory. Requires "path" (just the folder name).
- "search_documents": answer a question using the user's indexed documents. Requires "query".
- "locate_file": find the location of a file by meaning/content. Requires "query".
- "delete": permanently delete a file or folder. Requires "path". Use only when the user clearly asks to delete/remove something.
- "find_duplicates": scan a directory for duplicate files by content. Requires "path".
- "photo_search": search photos by semantic meaning. Requires "query".

Respond with ONLY valid JSON, nothing else, in this exact format:
{"tool": "move", "src": "Meeting Notes", "dest": "documents"}
or
{"tool": "scan", "path": "DCIM"}
or
{"tool": "rename", "src": "old name.pdf", "new_name": "new name.pdf"}
or
{"tool": "insights", "path": "WhatsApp"}
or
{"tool": "locate_file", "query": "what to search for"}
or
{"tool": "search_documents", "query": "the user's question"}
or
{"tool": "delete", "path": "<path to delete>"}
or
{"tool": "find_duplicates", "path": "<directory path>"}
or
or
{"tool": "find_duplicates", "path": "<directory path>"}

If you cannot determine a clear command, respond with:
{"tool": "unknown", "reason": "<why>"}
"""

def get_intent(user_query: str):
    """
    Send a natural language query to the local LLM and get back
    a structured tool-call dict.
    """
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.1
    }

    try:
        response = requests.post(LLAMA_SERVER_URL, json=payload, timeout=360)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"tool": "error", "reason": f"Could not reach LLM server: {e}"}

    data = response.json()
    raw_text = data["choices"][0]["message"]["content"].strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        intent = json.loads(raw_text)
    except json.JSONDecodeError:
        return {"tool": "error", "reason": f"Could not parse LLM output: {raw_text}"}

    return intent


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:])
    if not query:
        print("Usage: python llm.py <natural language command>")
        sys.exit(1)

    result = get_intent(query)
    print(json.dumps(result, indent=2))
