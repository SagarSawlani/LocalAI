import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-file-manager")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-file-manager", "agent")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-file-manager", "tools")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "document_search")))

from fastapi import FastAPI
from routes import router as agent_router
from document_search.routes import router as docs_router  # adjust based on actual import
from document_search.audio_routes import router as audio_router

app = FastAPI()

app.include_router(agent_router)
app.include_router(docs_router)
app.include_router(audio_router)
