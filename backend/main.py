import sys
from pathlib import Path
# Add backend/ directory to path so absolute imports work when running as `uvicorn backend.main:app`
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import sessions, tests

app = FastAPI(title="AP CSA Tutor API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(tests.router,    prefix="/api/tests",    tags=["tests"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
# Add in Phase 2: from routers import audio; app.include_router(audio.router, ...)
# Add in Phase 3: from routers import ai;    app.include_router(ai.router, ...)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
