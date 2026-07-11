import requests
import json

LLAMA_SERVER_URL = "http://localhost:8080/v1/chat/completions"

SYSTEM_PROMPT = """You are a file management assistant. Convert the user's natural language request into a JSON command.

Available tools:
- "move": move a file/folder. Requires "src" and "dest" (both full paths).
- "scan": list contents of a directory. Requires "path".

Respond with ONLY valid JSON, nothing else, in this exact format:
{"tool": "move", "src": "<source path>", "dest": "<destination path>"}
or
{"tool": "scan", "path": "<directory path>"}

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
        response = requests.post(LLAMA_SERVER_URL, json=payload, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"tool": "error", "reason": f"Could not reach LLM server: {e}"}

    data = response.json()
    raw_text = data["choices"][0]["message"]["content"].strip()

    # Strip markdown code fences if the model adds them
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