import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-file-manager")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-file-manager", "agent")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-file-manager", "tools")))

from fastapi import FastAPI
from routes import router as agent_router

app = FastAPI()

app.include_router(agent_router)