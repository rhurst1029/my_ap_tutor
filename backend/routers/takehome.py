"""
Serve take-home assignment files (JSON, Java) for the TakeHomeRunner UI.
Files are read from data/students/{student_dir}/take_home_{session}/.
"""
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from config import STUDENTS_DIR

router = APIRouter()


@router.get("/{student_dir}/{assignment}/{rest:path}")
async def serve_takehome_file(student_dir: str, assignment: str, rest: str):
    """Serve a file from a student's take-home directory."""
    # Validate path components to prevent traversal
    if ".." in student_dir or ".." in assignment or ".." in rest:
        raise HTTPException(400, "Invalid path")
    if not re.match(r'^[a-z0-9_]+_data$', student_dir):
        raise HTTPException(400, "Invalid student directory")
    if not re.match(r'^take_home_session_\d+$', assignment):
        raise HTTPException(400, "Invalid assignment directory")

    file_path = STUDENTS_DIR / student_dir / assignment / rest
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, f"File not found: {rest}")

    # Serve based on extension
    suffix = file_path.suffix.lower()
    if suffix == '.json':
        return JSONResponse(content=__import__('json').loads(file_path.read_text()))
    elif suffix == '.java':
        return PlainTextResponse(content=file_path.read_text(), media_type="text/plain")
    else:
        return PlainTextResponse(content=file_path.read_text())
