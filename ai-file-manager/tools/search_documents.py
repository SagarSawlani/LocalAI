# agent/tools/search_documents.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend/document_search")))
from qa import answer_question

def search_documents(query: str) -> dict:
    result = answer_question(query)
    return {"tool": "search_documents", **result}