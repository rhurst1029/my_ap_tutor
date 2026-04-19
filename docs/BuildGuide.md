# AP Computer Science A — Interactive Learning Management Tool
## Build Guide v1.0

This guide is the complete specification for a coding agent to build an iterative, interactive
AP CSA learning management tool. Follow phases in order. Do not skip phases.

---

## Overview

The tool runs a 3-step iteration loop:
  1. GAUGE      — Student takes an AP CSA test (one question at a time, guiding questions answered verbally)
  2. TEACH      — System generates a performance report, study guide, and interactive study module
  3. RE-ASSESS  — Claude generates a new adaptive test targeting weak areas; loop repeats

Each iteration after the first references the student's full session history.

---

## Tech Stack

- Frontend:       React + TypeScript (Vite), Monaco editor
- Backend:        Python FastAPI
- Speech-to-text: Vosk (local, offline — no cloud required)
- AI:             Claude API (Anthropic) — reports, study guides, test generation, Q&A chat
- Auth:           Simple name entry only — data stored in {name}_data/ folders
- Java execution: Pre-computed traces in JSON (Phases 1-3); live JDI tracer optional (Phase 4)

---

## Full Directory and File Structure

```
APCompSci/
├── BuildGuide.md                           <- this file
├── .gitignore                              <- update to include backend/venv, data/students, .env
├── src/Main.java                           <- leave untouched (existing example)
│
├── backend/
│   ├── main.py                             <- FastAPI app entry point
│   ├── config.py                           <- env vars, paths, constants
│   ├── requirements.txt
│   ├── .env                                <- ANTHROPIC_API_KEY (gitignored)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── sessions.py                     <- session start/save/history
│   │   ├── tests.py                        <- test loading + answer checking
│   │   ├── audio.py                        <- audio upload + Vosk transcription
│   │   ├── visualizer.py                   <- live Java trace (Phase 4)
│   │   └── ai.py                           <- report, study guide, chat, test gen
│   ├── services/
│   │   ├── __init__.py
│   │   ├── docx_converter.py               <- .docx -> JSON (run via scripts/)
│   │   ├── session_manager.py              <- read/write student data folders
│   │   ├── vosk_transcriber.py             <- Vosk model loading + transcription
│   │   ├── java_tracer.py                  <- subprocess call to tracer JAR
│   │   └── claude_service.py               <- all Anthropic API calls
│   ├── prompts/
│   │   ├── report_prompt.txt
│   │   ├── study_guide_prompt.txt
│   │   ├── test_gen_prompt.txt
│   │   └── chat_system_prompt.txt
│   └── models/
│       ├── __init__.py
│       ├── question.py
│       ├── session.py
│       └── report.py
│
├── java-tracer/                            <- standalone Java trace tool (Phase 4)
│   ├── Tracer.java
│   ├── TraceStep.java
│   └── build.sh
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       │   ├── client.ts
│       │   ├── sessions.ts
│       │   ├── tests.ts
│       │   ├── audio.ts
│       │   └── ai.ts
│       ├── components/
│       │   ├── NameEntry.tsx
│       │   ├── TestRunner/
│       │   │   ├── TestRunner.tsx          <- orchestrates question-by-question flow
│       │   │   ├── QuestionCard.tsx        <- renders a single question
│       │   │   ├── MultipleChoice.tsx
│       │   │   ├── FreeResponse.tsx
│       │   │   ├── CodeTrace.tsx           <- wrapper for code_trace questions
│       │   │   ├── JavaVisualizer.tsx      <- Monaco + step-through + variable panel
│       │   │   ├── VariablePanel.tsx       <- call stack / variable state diagram
│       │   │   └── AudioCapture.tsx        <- MediaRecorder widget per guiding Q
│       │   └── StudyModule/
│       │       ├── StudyModule.tsx         <- tab container
│       │       ├── ReportView.tsx
│       │       ├── Flashcards.tsx
│       │       ├── MiniQuiz.tsx
│       │       └── ChatInterface.tsx       <- streaming Claude Q&A
│       ├── hooks/
│       │   ├── useStudentSession.ts
│       │   ├── useAudioRecorder.ts
│       │   └── useStreamingChat.ts
│       ├── store/
│       │   └── sessionStore.ts             <- Zustand global state
│       └── types/
│           ├── question.ts
│           ├── session.ts
│           └── report.ts
│
├── data/
│   ├── tests/
│   │   ├── ap_csa_test_1.json              <- converted from bella_ap_csa_test.docx
│   │   └── (generated adaptive tests appear here)
│   ├── students/
│   │   └── (bella_data/, etc. created at runtime)
│   └── vosk-model/
│       └── vosk-model-small-en-us-0.15/   <- download separately (~50MB)
│
└── scripts/
    ├── convert_docx.py                     <- one-shot .docx -> JSON conversion
    └── validate_json.py                    <- validates test JSON against schema
```

---

## JSON Schemas

### Question Schema — data/tests/ap_csa_test_1.json

```json
{
  "$schema": "ap_csa_question_schema_v1",
  "test_id": "ap_csa_test_1",
  "title": "AP Computer Science A — Diagnostic Test",
  "created_at": "2026-04-11",
  "source": "converted_docx",
  "questions": [
    {
      "id": "q1",
      "type": "multiple_choice",
      "topic_tags": ["arrays", "loops"],
      "difficulty": "medium",
      "text": "What is the output of the following code?",
      "code_block": null,
      "options": ["A) 5", "B) 10", "C) 15", "D) 20"],
      "answer_key": "B",
      "explanation": "The loop iterates...",
      "guiding_questions": [
        {
          "id": "q1_g1",
          "text": "Walk me through what happens on each iteration.",
          "intent": "Check understanding of loop variable tracking"
        },
        {
          "id": "q1_g2",
          "text": "What value does i hold after the third iteration?",
          "intent": "Probe specific variable state"
        }
      ],
      "execution_trace": null
    },
    {
      "id": "q2",
      "type": "code_trace",
      "topic_tags": ["methods", "parameter_passing", "call_stack"],
      "difficulty": "hard",
      "text": "What is printed when the following program runs?",
      "code_block": "public class Main {\n  public static void main(String[] args) {\n    int a = 10;\n    int b = 5;\n    doubleValues(a, b);\n    System.out.print(b);\n    System.out.print(a);\n  }\n  public static void doubleValues(int c, int d) {\n    c = c * 2;\n    d = d * 2;\n    System.out.print(c);\n    System.out.print(d);\n  }\n}",
      "options": ["A) 2010510", "B) 20105", "C) 10205", "D) 201051010"],
      "answer_key": "B",
      "explanation": "Java passes primitives by value. c and d are copies of a and b. Changes inside doubleValues do not affect a and b in main.",
      "guiding_questions": [
        {
          "id": "q2_g1",
          "text": "When doubleValues is called, are a and b changed?",
          "intent": "Test pass-by-value understanding"
        },
        {
          "id": "q2_g2",
          "text": "Draw the call stack when System.out.print(c) runs. What is in each frame?",
          "intent": "Test call stack visualization"
        }
      ],
      "execution_trace": [
        {
          "step": 0,
          "line_number": 3,
          "description": "Declare int a = 10",
          "stack_frames": [{"method": "main", "variables": {"a": 10}}],
          "output_so_far": ""
        },
        {
          "step": 1,
          "line_number": 4,
          "description": "Declare int b = 5",
          "stack_frames": [{"method": "main", "variables": {"a": 10, "b": 5}}],
          "output_so_far": ""
        },
        {
          "step": 2,
          "line_number": 5,
          "description": "Call doubleValues(a, b) — copies of a and b passed as c and d",
          "stack_frames": [
            {"method": "main", "variables": {"a": 10, "b": 5}},
            {"method": "doubleValues", "variables": {"c": 10, "d": 5}}
          ],
          "output_so_far": ""
        },
        {
          "step": 3,
          "line_number": 10,
          "description": "c = c * 2 -> c becomes 20",
          "stack_frames": [
            {"method": "main", "variables": {"a": 10, "b": 5}},
            {"method": "doubleValues", "variables": {"c": 20, "d": 5}}
          ],
          "output_so_far": ""
        },
        {
          "step": 4,
          "line_number": 11,
          "description": "d = d * 2 -> d becomes 10",
          "stack_frames": [
            {"method": "main", "variables": {"a": 10, "b": 5}},
            {"method": "doubleValues", "variables": {"c": 20, "d": 10}}
          ],
          "output_so_far": ""
        },
        {
          "step": 5,
          "line_number": 12,
          "description": "System.out.print(c) -> prints 20",
          "stack_frames": [
            {"method": "main", "variables": {"a": 10, "b": 5}},
            {"method": "doubleValues", "variables": {"c": 20, "d": 10}}
          ],
          "output_so_far": "20"
        },
        {
          "step": 6,
          "line_number": 13,
          "description": "System.out.print(d) -> prints 10",
          "stack_frames": [
            {"method": "main", "variables": {"a": 10, "b": 5}},
            {"method": "doubleValues", "variables": {"c": 20, "d": 10}}
          ],
          "output_so_far": "2010"
        },
        {
          "step": 7,
          "line_number": 6,
          "description": "doubleValues returns; back in main. a and b are unchanged.",
          "stack_frames": [{"method": "main", "variables": {"a": 10, "b": 5}}],
          "output_so_far": "2010"
        },
        {
          "step": 8,
          "line_number": 6,
          "description": "System.out.print(b) -> prints 5",
          "stack_frames": [{"method": "main", "variables": {"a": 10, "b": 5}}],
          "output_so_far": "20105"
        },
        {
          "step": 9,
          "line_number": 7,
          "description": "System.out.print(a) -> prints 10",
          "stack_frames": [{"method": "main", "variables": {"a": 10, "b": 5}}],
          "output_so_far": "2010510"
        }
      ]
    }
  ]
}
```

Valid values for `type`: "multiple_choice", "free_response", "code_trace"

Valid values for `topic_tags` (use ONLY these strings):
  variables_and_types, operators, conditionals, loops, arrays, 2d_arrays,
  methods, parameter_passing, strings, classes_and_objects, inheritance,
  polymorphism, recursion, arraylist, searching_sorting, interfaces

### Session Response Schema — data/students/bella_data/session_1/responses.json

```json
{
  "session_id": "session_1",
  "student_name": "bella",
  "test_id": "ap_csa_test_1",
  "iteration": 1,
  "started_at": "2026-04-11T14:30:00Z",
  "completed_at": "2026-04-11T15:00:00Z",
  "responses": [
    {
      "question_id": "q1",
      "selected_answer": "B",
      "free_response_text": null,
      "is_correct": true,
      "time_spent_seconds": 45,
      "guiding_question_responses": [
        {
          "guiding_question_id": "q1_g1",
          "audio_file": "q1_g1.wav",
          "transcript": "On each iteration i starts at zero and goes up by one...",
          "transcript_confidence": 0.87
        }
      ]
    }
  ]
}
```

### Session Metadata Schema — data/students/bella_data/session_1/metadata.json

```json
{
  "session_id": "session_1",
  "student_name": "bella",
  "test_id": "ap_csa_test_1",
  "iteration": 1,
  "timestamp": "2026-04-11T14:30:00Z",
  "total_questions": 15,
  "completed": true,
  "completed_at": "2026-04-11T15:00:00Z",
  "study_completed": false
}
```

### Report Schema — data/students/bella_data/report_1.json

```json
{
  "report_id": "report_1",
  "student_name": "bella",
  "iteration": 1,
  "generated_at": "2026-04-11T15:05:00Z",
  "overall_score_percent": 67,
  "topic_analysis": [
    {
      "topic": "parameter_passing",
      "questions_attempted": 3,
      "questions_correct": 1,
      "strength_level": "weak",
      "feedback": "You consistently selected answers assuming pass-by-reference. In Java, primitive types are always passed by value..."
    }
  ],
  "strengths_summary": "Strong array manipulation and basic loop comprehension.",
  "weaknesses_summary": "Needs work on: parameter passing, inheritance, and 2D arrays.",
  "weak_topics": ["parameter_passing", "inheritance", "2d_arrays"],
  "actionable_steps": [
    "Review how Java copies primitive values into method parameters.",
    "Practice tracing code with multiple method calls on paper before running it."
  ],
  "verbal_response_notes": "Your verbal explanation for q2 showed awareness that something changes but uncertainty about which frame is modified."
}
```

### Study Guide Schema — data/students/bella_data/study_guide_1.json

```json
{
  "study_guide_id": "study_guide_1",
  "student_name": "bella",
  "iteration": 1,
  "generated_at": "2026-04-11T15:06:00Z",
  "weak_topics": ["parameter_passing", "inheritance"],
  "reading_summaries": [
    {
      "topic": "parameter_passing",
      "title": "How Java Passes Arguments to Methods",
      "content": "In Java, when you call a method and pass a primitive (int, double, boolean, char), Java makes a copy of the value..."
    }
  ],
  "flashcards": [
    {
      "id": "fc1",
      "topic": "parameter_passing",
      "front": "What happens to the original variable when you pass an int to a method?",
      "back": "Nothing. Java passes a copy of the value. The method works on its own local copy."
    }
  ],
  "mini_quiz": [
    {
      "id": "mq1",
      "topic": "parameter_passing",
      "type": "multiple_choice",
      "text": "After calling swap(a, b) where a=3 and b=7, what are the values of a and b in the caller?",
      "options": ["A) a=7, b=3", "B) a=3, b=7", "C) a=0, b=0", "D) Depends on swap"],
      "answer_key": "B",
      "explanation": "Primitives are passed by value, so the caller's a and b are unaffected."
    }
  ]
}
```

---

## Complete API Endpoint Reference

```
GET  /api/health

# Tests
GET  /api/tests/
     returns: [{ "test_id": "ap_csa_test_1", "title": "..." }]

GET  /api/tests/{test_id}
     returns: full test JSON including answer_key

POST /api/tests/{test_id}/check/{question_id}
     body:    { "answer": "B" }
     returns: { "is_correct": true, "correct_answer": "B" }

# Sessions
POST /api/sessions/start
     body:    { "student_name": "bella", "test_id": "ap_csa_test_1", "total_questions": 15 }
     returns: { "session_id": "session_1", "iteration": 1 }

POST /api/sessions/{name}/{session_id}/save
     body:    SessionSaveRequest (see Pydantic models section)
     returns: { "status": "saved" }

PATCH /api/sessions/{name}/{session_id}/mark-study-complete
     returns: { "status": "updated" }

GET  /api/sessions/{name}/history
     returns: { "sessions": [...metadata], "reports": [...reports] }

# Audio
POST /api/audio/{name}/{session_id}/upload?question_id=q1&guiding_id=q1_g1
     body:    multipart/form-data, field name "file", content type audio/webm
     returns: { "filename": "q1_g1.wav", "transcript": "...", "confidence": 0.87 }

# Visualizer (Phase 4 only)
POST /api/visualizer/trace
     body:    { "code": "<Java source string>" }
     returns: array of TraceStep objects

# AI / Claude
POST /api/ai/{name}/{session_id}/report
     returns: full report JSON (also saved to disk)

POST /api/ai/{name}/{session_id}/study-guide
     returns: full study guide JSON (also saved to disk)

POST /api/ai/chat
     body:    { "student_name": "bella", "messages": [...], "weak_topics": [...], "weaknesses_summary": "..." }
     returns: text/event-stream — each chunk: "data: {\"text\": \"...\"}\n\n", ends with "data: [DONE]\n\n"

POST /api/ai/{name}/generate-test
     body:    { "student_name": "bella", "total_questions": 15 }
     returns: { "test_id": "...", "test_filename": "...", "iteration": 2, "weak_topics_targeted": [...] }

# Take-Home (in-browser IDE at /?takehome={student_dir}/{assignment})
GET  /api/takehome/{student_dir}/{assignment}/{rest:path}
     Serves JSON and Java files from data/students/{student_dir}/{assignment}/
     Path validation:
       - student_dir must match ^[a-z0-9_]+_data$
       - assignment must match ^take_home_session_\d+$
       - rest must not contain ".."
     Extensions served: .json (application/json), .java (text/plain), others (text/plain)
     Returns 404 if file missing, 400 on invalid path component.
```

---

## Phase 1: MVP — Core Test Flow

### Step 1.1 — Install Prerequisites

```bash
# Node 20 via nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.zshrc
nvm install 20 && nvm use 20

# Python 3.11 via pyenv
curl https://pyenv.run | bash
# Add to ~/.zshrc:
#   export PATH="$HOME/.pyenv/bin:$PATH"
#   eval "$(pyenv init -)"
source ~/.zshrc
pyenv install 3.11.9
pyenv local 3.11.9   # run from APCompSci/ directory

# Python virtual env
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

System dependency — ffmpeg (required by pydub in Phase 2):
  Download from ffmpeg.org or run: brew install ffmpeg
  Verify: ffmpeg -version

### Step 1.2 — backend/requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9
python-dotenv==1.0.1
anthropic==0.28.0
vosk==0.3.45
python-docx==1.1.2
pydantic==2.7.1
aiofiles==23.2.1
httpx==0.27.0
pydub==0.25.1
```

### Step 1.3 — .docx to JSON Conversion (scripts/convert_docx.py)

CRITICAL: Run in two passes. Never skip Pass 1.

Pass 1 — Structural inspection. Run FIRST. Read all output before writing any parsing logic.

```python
# scripts/convert_docx.py
import json, sys, os
from pathlib import Path
from docx import Document

DOCX_PATH  = Path(__file__).parent.parent / "bella_ap_csa_test.docx"
GUIDE_PATH = Path(__file__).parent.parent / "bella_tutor_guide.docx"
OUTPUT_PATH = Path(__file__).parent.parent / "data/tests/ap_csa_test_1.json"

def inspect_document(path: Path):
    doc = Document(str(path))
    print(f"\n=== PARAGRAPHS in {path.name} ===")
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip():
            fonts = list({run.font.name for run in para.runs if run.font.name})
            print(f"[P{i:03d}] style={para.style.name!r:30s} fonts={fonts} text={para.text[:80]!r}")
    print(f"\n=== TABLES in {path.name} ===")
    for i, table in enumerate(doc.tables):
        print(f"[Table {i}] {len(table.rows)} rows x {len(table.columns)} cols")
        for row in table.rows:
            print("  row:", [c.text.strip()[:40] for c in row.cells])

if __name__ == "__main__":
    if "--inspect" in sys.argv:
        inspect_document(DOCX_PATH)
        inspect_document(GUIDE_PATH)
        sys.exit(0)
    # Pass 2: implement extract_questions() after reading inspect output
    raise NotImplementedError("Implement extract_questions() after running --inspect first")
```

Run: `python scripts/convert_docx.py --inspect`

Pass 2 — Implement `extract_questions()` based on what --inspect revealed. Match the actual
document structure. Common patterns:
  - Question boundaries: numbered paragraphs "1." or style like "List Number"
  - Code blocks: style named "Code" OR runs with font.name == "Courier New"
  - MC options: paragraphs starting with "A)", "B)", "C)", "D)"
  - Answer key: separate section in the tutor guide, matched by question number
  - Guiding questions: in bella_tutor_guide.docx, grouped per question number

After extraction, call Claude to assign topic_tags per question:

```python
import anthropic
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

VALID_TOPICS = [
    "variables_and_types", "operators", "conditionals", "loops",
    "arrays", "2d_arrays", "methods", "parameter_passing", "strings",
    "classes_and_objects", "inheritance", "polymorphism", "recursion",
    "arraylist", "searching_sorting", "interfaces"
]

def assign_topics(question_text: str, code_block: str | None) -> list[str]:
    content = question_text + ("\n" + code_block if code_block else "")
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content":
            f"Given this AP CSA question, return a JSON array of topic tags "
            f"from this list ONLY: {VALID_TOPICS}\n"
            f"Question: {content}\n"
            f"Return only the JSON array, no explanation, no markdown."}]
    )
    text = msg.content[0].text.strip().strip("```json").strip("```").strip()
    return json.loads(text)
```

Run conversion: `python scripts/convert_docx.py`
Validate output: `python scripts/validate_json.py data/tests/ap_csa_test_1.json`

### Step 1.4 — backend/config.py

```python
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR     = Path(__file__).parent.parent
DATA_DIR     = BASE_DIR / "data"
TESTS_DIR    = DATA_DIR / "tests"
STUDENTS_DIR = DATA_DIR / "students"
VOSK_MODEL_DIR = DATA_DIR / "vosk-model" / "vosk-model-small-en-us-0.15"
JAVA_TRACER_JAR = BASE_DIR / "java-tracer" / "out" / "tracer.jar"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL      = "claude-opus-4-6"
CLAUDE_CHAT_MODEL = "claude-sonnet-4-6"   # faster/cheaper for streaming chat
```

### Step 1.5 — backend/main.py

```python
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
```

### Step 1.6 — backend/routers/tests.py

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from config import TESTS_DIR

router = APIRouter()

@router.get("/")
async def list_tests():
    return [
        {"test_id": json.loads(f.read_text())["test_id"],
         "title":   json.loads(f.read_text())["title"]}
        for f in TESTS_DIR.glob("*.json")
    ]

@router.get("/{test_id}")
async def get_test(test_id: str):
    path = TESTS_DIR / f"{test_id}.json"
    if not path.exists():
        raise HTTPException(404, "Test not found")
    return json.loads(path.read_text())

class AnswerCheckRequest(BaseModel):
    answer: str

@router.post("/{test_id}/check/{question_id}")
async def check_answer(test_id: str, question_id: str, body: AnswerCheckRequest):
    path = TESTS_DIR / f"{test_id}.json"
    if not path.exists():
        raise HTTPException(404, "Test not found")
    data = json.loads(path.read_text())
    q = next((q for q in data["questions"] if q["id"] == question_id), None)
    if not q:
        raise HTTPException(404, "Question not found")
    return {"is_correct": body.answer == q["answer_key"], "correct_answer": q["answer_key"]}
```

### Step 1.7 — backend/models/session.py

```python
from pydantic import BaseModel
from typing import Optional

class SessionStartRequest(BaseModel):
    student_name: str
    test_id: str
    total_questions: int

class GuidingQuestionResponse(BaseModel):
    guiding_question_id: str
    audio_file: Optional[str] = None
    transcript: Optional[str] = None
    transcript_confidence: Optional[float] = None

class QuestionResponse(BaseModel):
    question_id: str
    question_type: Literal["multiple_choice", "code_trace", "frq"] = "multiple_choice"
    selected_answer: Optional[str] = None        # MC / code_trace final answer
    frq_parts: list[FRQPartResponse] = []        # FRQ only
    is_correct: bool
    attempt_number: int = 1                      # 1 = first try, 2 = second try
    score_weight: float = 1.0                    # 1.0 | 0.7 | 0.0
    time_spent_seconds: int
    guiding_question_responses: list[GuidingQuestionResponse] = []

class SessionSaveRequest(BaseModel):
    session_id: str
    student_name: str
    test_id: str
    iteration: int
    started_at: str
    completed_at: str
    responses: list[QuestionResponse]
```

### Step 1.8 — backend/routers/sessions.py

```python
import re, json
from fastapi import APIRouter, HTTPException
from pathlib import Path
from datetime import datetime, timezone
from config import STUDENTS_DIR
from models.session import SessionStartRequest, SessionSaveRequest

router = APIRouter()

def get_student_dir(name: str) -> Path:
    safe = re.sub(r'[^\w]', '_', name.lower().strip())
    return STUDENTS_DIR / f"{safe}_data"

def next_iteration(student_dir: Path) -> int:
    return len([d for d in student_dir.glob("session_*") if d.is_dir()]) + 1

@router.post("/start")
async def start_session(req: SessionStartRequest):
    student_dir = get_student_dir(req.student_name)
    iteration   = next_iteration(student_dir)
    session_id  = f"session_{iteration}"
    session_dir = student_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "audio").mkdir(exist_ok=True)
    metadata = {
        "session_id": session_id,
        "student_name": req.student_name,
        "test_id": req.test_id,
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_questions": req.total_questions,
        "completed": False,
        "study_completed": False
    }
    (session_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return {"session_id": session_id, "iteration": iteration}

@router.post("/{student_name}/{session_id}/save")
async def save_responses(student_name: str, session_id: str, req: SessionSaveRequest):
    session_dir = get_student_dir(student_name) / session_id
    if not session_dir.exists():
        raise HTTPException(404, "Session not found")
    (session_dir / "responses.json").write_text(json.dumps(req.dict(), indent=2))
    meta_path = session_dir / "metadata.json"
    meta = json.loads(meta_path.read_text())
    meta["completed"]    = True
    meta["completed_at"] = datetime.now(timezone.utc).isoformat()
    meta_path.write_text(json.dumps(meta, indent=2))
    return {"status": "saved"}

@router.patch("/{student_name}/{session_id}/mark-study-complete")
async def mark_study_complete(student_name: str, session_id: str):
    meta_path = get_student_dir(student_name) / session_id / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(404, "Session not found")
    meta = json.loads(meta_path.read_text())
    meta["study_completed"] = True
    meta_path.write_text(json.dumps(meta, indent=2))
    return {"status": "updated"}

@router.get("/{student_name}/history")
async def get_history(student_name: str):
    student_dir = get_student_dir(student_name)
    if not student_dir.exists():
        return {"sessions": [], "reports": []}
    sessions = [json.loads((d / "metadata.json").read_text())
                for d in sorted(student_dir.glob("session_*"))
                if (d / "metadata.json").exists()]
    reports  = [json.loads(p.read_text()) for p in sorted(student_dir.glob("report_*.json"))]
    return {"sessions": sessions, "reports": reports}
```

### Step 1.9 — Frontend Initialization

```bash
cd /Users/ryanhurst/Desktop/APTutoring/MyAPTutor
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install axios zustand react-router-dom
```

frontend/vite.config.ts:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://localhost:8000' } }
})
```

### Step 1.10 — Core Frontend Components

frontend/src/App.tsx — state machine:
```typescript
type AppView = 'name_entry' | 'test' | 'study' | 'generating_test'

interface AppState {
  studentName: string
  sessionId: string
  testId: string
  iteration: number
}
```

frontend/src/components/NameEntry.tsx:
  - Text input for name
  - On submit: call GET /api/sessions/{name}/history
  - If history exists, show: "Welcome back {name}! Last score: {score}%. Weak areas: {topics}"
  - Then proceed to test

frontend/src/components/TestRunner/TestRunner.tsx:
  1. On mount: fetch GET /api/tests/{test_id}
  2. Call POST /api/sessions/start -> store session_id
  3. Display questions one at a time via QuestionCard
  4. Track responses in local state: QuestionResponse[]
  5. Show progress indicator: "Question 3 of 15"
  6. On final answer: call POST /api/sessions/{name}/{session_id}/save
  7. Transition to StudyModule view

frontend/src/components/TestRunner/QuestionCard.tsx:
  Receives: question object + onAnswer callback
  Routes by question.type:
    "multiple_choice" -> MultipleChoice component
    "free_response"   -> FreeResponse (textarea + submit button)
    "code_trace"      -> CodeTrace wrapper
      - Phase 1: render code_block in <pre> tag; show guiding questions as text labels
      - Phase 2: upgrade CodeTrace to use JavaVisualizer + AudioCapture

  IMPORTANT: Never show answer_key to the student before they answer.
  Grade server-side via POST /api/tests/{id}/check/{qid} after answer submission,
  or batch-grade all answers when saving the session.

### Step 1.11 — Run Commands (Phase 1)

```bash
# Terminal 1 — Backend
cd /Users/ryanhurst/Desktop/APTutoring/MyAPTutor
source backend/venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd /Users/ryanhurst/Desktop/APTutoring/MyAPTutor/frontend
npm run dev
```

Verify Phase 1 complete: enter name -> take test -> confirm responses.json saved to
data/students/{name}_data/session_1/responses.json

---

## Phase 2: Java Visualizer + Audio

### Step 2.1 — Monaco Editor Setup

```bash
cd frontend
npm install @monaco-editor/react monaco-editor
```

frontend/src/components/TestRunner/JavaVisualizer.tsx:

```tsx
import Editor from '@monaco-editor/react'
import { useState, useRef, useEffect } from 'react'
import type * as Monaco from 'monaco-editor'
import { VariablePanel } from './VariablePanel'

interface TraceStep {
  step: number
  line_number: number
  description: string
  stack_frames: Array<{ method: string; variables: Record<string, unknown> }>
  output_so_far: string
}

interface Props {
  codeBlock: string
  trace: TraceStep[] | null
}

export function JavaVisualizer({ codeBlock, trace }: Props) {
  const [stepIndex, setStepIndex] = useState(0)
  const editorRef   = useRef<Monaco.editor.IStandaloneCodeEditor | null>(null)
  const decorations = useRef<string[]>([])
  const monacoRef   = useRef<typeof Monaco | null>(null)
  const currentStep = trace ? trace[stepIndex] : null

  useEffect(() => {
    if (!editorRef.current || !monacoRef.current || !currentStep) return
    const monaco = monacoRef.current
    decorations.current = editorRef.current.deltaDecorations(
      decorations.current,
      [{
        range: new monaco.Range(currentStep.line_number, 1, currentStep.line_number, 1),
        options: { isWholeLine: true, className: 'highlighted-line' }
      }]
    )
  }, [stepIndex, currentStep])

  return (
    <div className="visualizer-container">
      <Editor
        height="300px"
        language="java"
        value={codeBlock}
        options={{ readOnly: true, minimap: { enabled: false }, fontSize: 14,
                   fontFamily: 'JetBrains Mono, Fira Code, monospace' }}
        onMount={(editor, monaco) => {
          editorRef.current = editor
          monacoRef.current = monaco
        }}
      />
      {trace && currentStep ? (
        <>
          <div className="trace-controls">
            <button onClick={() => setStepIndex(i => Math.max(0, i - 1))}
                    disabled={stepIndex === 0}>Prev</button>
            <span>Step {stepIndex + 1} / {trace.length}</span>
            <button onClick={() => setStepIndex(i => Math.min(trace.length - 1, i + 1))}
                    disabled={stepIndex === trace.length - 1}>Next</button>
          </div>
          <div className="step-description">{currentStep.description}</div>
          <div className="output-so-far">
            Output: <code>{currentStep.output_so_far || '(none yet)'}</code>
          </div>
          <VariablePanel stackFrames={currentStep.stack_frames} />
        </>
      ) : (
        <p className="no-trace">Step-through not available for this question.</p>
      )}
    </div>
  )
}
```

Add to global CSS: `.highlighted-line { background: rgba(255, 255, 0, 0.3); }`

frontend/src/components/TestRunner/VariablePanel.tsx:
Stack frames rendered bottom-to-top (main at bottom, deepest frame at top):

```tsx
interface StackFrame { method: string; variables: Record<string, unknown> }

export function VariablePanel({ stackFrames }: { stackFrames: StackFrame[] }) {
  return (
    <div className="variable-panel">
      <h4>Call Stack</h4>
      {[...stackFrames].reverse().map((frame, i) => (
        <div key={i} className={`stack-frame ${i === 0 ? 'active-frame' : ''}`}>
          <div className="frame-header">{frame.method}()</div>
          <table className="variable-table">
            <tbody>
              {Object.entries(frame.variables).map(([name, value]) => (
                <tr key={name}>
                  <td className="var-name">{name}</td>
                  <td className="var-value">{String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}
```

### Step 2.2 — Generate Execution Traces for Test 1

For every code_trace question in data/tests/ap_csa_test_1.json, generate an execution_trace.

Use this Claude prompt (call once per question after conversion):

```
Given this Java code snippet, produce a JSON array of execution trace steps.
Each step must have exactly these fields:
  { "step": <int>, "line_number": <int>, "description": "<string>",
    "stack_frames": [{"method": "<name>", "variables": {"<var>": <value>}}],
    "output_so_far": "<string>" }
Trace every statement in execution order.
Track ALL local variables in EVERY active stack frame at each step.
output_so_far is the cumulative printed output up to and including this step.
Return only raw JSON array, no markdown, no explanation.

Code:
<paste code_block here>
```

Store the resulting array in the question's execution_trace field in the JSON file.
For questions with no code_block or type != "code_trace", leave execution_trace as null.

### Step 2.3 — Vosk Audio Transcription

Download Vosk model (do not skip):
  URL: https://alphacephei.com/vosk/models
  File: vosk-model-small-en-us-0.15.zip (~50MB)
  Extract to: data/vosk-model/vosk-model-small-en-us-0.15/
  Verify the path: data/vosk-model/vosk-model-small-en-us-0.15/am/  (should exist)

backend/services/vosk_transcriber.py:

```python
from vosk import Model, KaldiRecognizer
import wave, json
from pathlib import Path
from config import VOSK_MODEL_DIR

_model = None

def get_model() -> Model:
    global _model
    if _model is None:
        if not VOSK_MODEL_DIR.exists():
            raise RuntimeError(
                f"Vosk model not found at {VOSK_MODEL_DIR}\n"
                "Download vosk-model-small-en-us-0.15 from alphacephei.com/vosk/models"
            )
        _model = Model(str(VOSK_MODEL_DIR))
    return _model

def transcribe_wav(wav_path: Path) -> dict:
    """Transcribe a 16kHz 16-bit mono WAV file. Returns {text, confidence}."""
    model = get_model()
    with wave.open(str(wav_path), "rb") as wf:
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)
        results = []
        while True:
            data = wf.readframes(4000)
            if not data:
                break
            if rec.AcceptWaveform(data):
                results.append(json.loads(rec.Result()))
        results.append(json.loads(rec.FinalResult()))
    full_text = " ".join(r.get("text", "") for r in results).strip()
    all_words  = [w for r in results for w in r.get("result", [])]
    confidence = (sum(w.get("conf", 1.0) for w in all_words) / len(all_words)
                  if all_words else (1.0 if full_text else 0.0))
    return {"text": full_text, "confidence": round(confidence, 3)}
```

backend/routers/audio.py:

```python
import re, json
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import aiofiles
from pydub import AudioSegment
from config import STUDENTS_DIR
from services.vosk_transcriber import transcribe_wav

router = APIRouter()

def get_student_dir(name: str) -> Path:
    safe = re.sub(r'[^\w]', '_', name.lower().strip())
    return STUDENTS_DIR / f"{safe}_data"

@router.post("/{student_name}/{session_id}/upload")
async def upload_audio(student_name: str, session_id: str,
                       question_id: str, guiding_id: str,
                       file: UploadFile = File(...)):
    audio_dir = get_student_dir(student_name) / session_id / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    webm_path = audio_dir / f"{question_id}_{guiding_id}.webm"
    wav_path  = audio_dir / f"{question_id}_{guiding_id}.wav"

    content = await file.read()
    async with aiofiles.open(webm_path, "wb") as f:
        await f.write(content)

    # Convert WebM/Opus -> 16kHz mono 16-bit WAV (required by Vosk)
    audio = AudioSegment.from_file(str(webm_path), format="webm")
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    audio.export(str(wav_path), format="wav")

    try:
        result = transcribe_wav(wav_path)
        return {"filename": wav_path.name,
                "transcript": result["text"],
                "confidence": result["confidence"]}
    except Exception as e:
        raise HTTPException(500, f"Transcription failed: {e}")
```

Register in main.py:
```python
from routers import audio
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
```

### Step 2.4 — AudioCapture.tsx

```tsx
import { useState, useRef } from 'react'
import axios from 'axios'

interface Props {
  studentName: string
  sessionId: string
  questionId: string
  guidingId: string
  onTranscript: (text: string, confidence: number) => void
}

export function AudioCapture({ studentName, sessionId, questionId, guidingId, onTranscript }: Props) {
  const [state, setState] = useState<'idle' | 'recording' | 'uploading' | 'done'>('idle')
  const [transcript, setTranscript] = useState('')
  const mrRef   = useRef<MediaRecorder | null>(null)
  const chunks  = useRef<Blob[]>([])

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mr = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })
    mrRef.current = mr
    chunks.current = []
    mr.ondataavailable = e => chunks.current.push(e.data)
    mr.onstop = async () => {
      setState('uploading')
      const blob = new Blob(chunks.current, { type: 'audio/webm' })
      const form = new FormData()
      form.append('file', blob, 'audio.webm')
      const res = await axios.post(
        `/api/audio/${studentName}/${sessionId}/upload?question_id=${questionId}&guiding_id=${guidingId}`,
        form
      )
      setTranscript(res.data.transcript)
      onTranscript(res.data.transcript, res.data.confidence)
      setState('done')
      stream.getTracks().forEach(t => t.stop())
    }
    mr.start()
    setState('recording')
  }

  return (
    <div className="audio-capture">
      {state === 'idle'      && <button onClick={start}>Record Answer</button>}
      {state === 'recording' && <button onClick={() => mrRef.current?.stop()} className="btn-recording">Stop Recording</button>}
      {state === 'uploading' && <span>Transcribing...</span>}
      {state === 'done'      && (
        <div>
          <p className="transcript">{transcript}</p>
          <button onClick={() => setState('idle')}>Re-record</button>
        </div>
      )}
    </div>
  )
}
```

Integrate into QuestionCard: for each guiding_question in question.guiding_questions,
render the guiding question text above an AudioCapture component. Store each transcript
in the session response state under guiding_question_responses.

---

## Phase 3: Claude AI Layer

### Step 3.1 — backend/.env

```
ANTHROPIC_API_KEY=your_key_here
```

Add to .gitignore: `.env`

### Step 3.2 — Claude Prompt Templates

backend/prompts/report_prompt.txt:
```
You are an expert AP Computer Science A tutor analyzing a student's test performance.

Student: {student_name}
Iteration: {iteration}

Question-by-question performance data:
{questions_json}

Return a JSON object with EXACTLY this structure.
Return only raw JSON — no markdown, no code fences, no explanation text.
{
  "overall_score_percent": <integer 0-100>,
  "topic_analysis": [
    {
      "topic": "<topic_name>",
      "questions_attempted": <int>,
      "questions_correct": <int>,
      "strength_level": "strong" | "moderate" | "weak",
      "feedback": "<2-3 sentence specific feedback referencing their actual answers>"
    }
  ],
  "strengths_summary": "<1-2 sentences on what the student does well>",
  "weaknesses_summary": "<1-2 sentences on what needs improvement>",
  "weak_topics": ["<topic1>", "<topic2>"],
  "actionable_steps": ["<specific step 1>", "<specific step 2>", "<specific step 3>"],
  "verbal_response_notes": "<observation about verbal answers if transcripts were provided, else empty string>"
}

weak_topics must include every topic with strength_level "weak" or "moderate".
Be specific. Reference the student's actual answer choices and verbal transcripts.
```

backend/prompts/study_guide_prompt.txt:
```
You are an expert AP Computer Science A tutor. Create a targeted study guide.

Student: {student_name}
Topics to focus on: {weak_topics}
Context on weaknesses: {weaknesses_summary}

Return a JSON object with EXACTLY this structure.
Return only raw JSON — no markdown, no code fences, no explanation text.
{
  "reading_summaries": [
    {
      "topic": "<topic_name>",
      "title": "<descriptive title>",
      "content": "<3-5 paragraphs of explanation at AP CSA level>"
    }
  ],
  "flashcards": [
    {
      "id": "fc<n>",
      "topic": "<topic_name>",
      "front": "<question or concept>",
      "back": "<answer or explanation>"
    }
  ],
  "mini_quiz": [
    {
      "id": "mq<n>",
      "topic": "<topic_name>",
      "type": "multiple_choice",
      "text": "<question>",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "answer_key": "<A|B|C|D>",
      "explanation": "<why this answer is correct>"
    }
  ]
}

Generate at least 3 flashcards and 2 mini_quiz questions per weak topic.
AP CSA level Java only. No features beyond AP CSA scope.
```

backend/prompts/test_gen_prompt.txt:
```
You are an expert AP Computer Science A test generator.

Student: {student_name}
This is iteration {iteration} (test number {iteration}).
Persistent weak topics to target: {weak_topics}
Previous test scores (oldest to newest): {previous_scores}
Previous session dates: {session_dates}

Generate a new adaptive test with these requirements:
- Exactly {total_questions} questions
- At least 60% of questions target the weak topics listed above
- Remaining 40% covers the full AP CSA scope for completeness
- Slightly harder difficulty than the previous iteration
- Mix of types: multiple_choice, free_response, code_trace
- 2-3 guiding questions per question (inspired by Socratic tutoring style)

Return a JSON object with EXACTLY this structure.
Return only raw JSON — no markdown, no code fences, no explanation text.
{
  "test_id": "adaptive_{student_name_lower}_iteration_{iteration}",
  "title": "AP CSA Adaptive Test — Iteration {iteration}",
  "created_at": "<today YYYY-MM-DD>",
  "source": "claude_generated",
  "weak_topics_targeted": {weak_topics_json},
  "questions": [
    {
      "id": "q<n>",
      "type": "multiple_choice" | "free_response" | "code_trace",
      "topic_tags": ["<tag>"],
      "difficulty": "easy" | "medium" | "hard",
      "text": "<question text>",
      "code_block": "<Java code string or null>",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."] or null,
      "answer_key": "<A|B|C|D, or the free response answer>",
      "explanation": "<explanation of the correct answer>",
      "guiding_questions": [
        {
          "id": "q<n>_g<m>",
          "text": "<guiding question>",
          "intent": "<what conceptual gap this probes>"
        }
      ],
      "execution_trace": null
    }
  ]
}

Always set execution_trace to null.
Use realistic Java code at AP CSA level only (no generics, no lambdas, no streams).
topic_tags must come from this list only:
  variables_and_types, operators, conditionals, loops, arrays, 2d_arrays,
  methods, parameter_passing, strings, classes_and_objects, inheritance,
  polymorphism, recursion, arraylist, searching_sorting, interfaces
```

backend/prompts/chat_system_prompt.txt:
```
You are a supportive, patient AP Computer Science A tutor named Alex.

You are helping {student_name} who has just completed a test.
Their weak areas: {weak_topics}
Weakness context: {weaknesses_summary}

Guidelines:
- Answer questions about Java and AP CSA concepts, focused on the weak topics above
- Use short, runnable Java code examples at AP CSA level
- Ask Socratic follow-up questions to probe understanding
- Reference the student's specific mistakes when relevant
- Be encouraging but honest about gaps
- Keep responses focused and concise
- Gently redirect if asked about topics outside AP CSA scope
```

### Step 3.3 — backend/services/claude_service.py

```python
import re, json
from pathlib import Path
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_CHAT_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text()

def _parse_json(text: str):
    """Strip markdown code fences if present, then parse JSON."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    return json.loads(text.strip())

def generate_report(session_data: dict, test_data: dict) -> dict:
    summaries = []
    for r in session_data["responses"]:
        q = next(q for q in test_data["questions"] if q["id"] == r["question_id"])
        summaries.append({
            "question_id": q["id"],
            "topic_tags": q["topic_tags"],
            "selected_answer": r.get("selected_answer"),
            "correct_answer": q["answer_key"],
            "is_correct": r["is_correct"],
            "question_text": q["text"][:200],
            "verbal_responses": [
                f"{gr['guiding_question_id']}: {gr.get('transcript', '[no audio]')}"
                for gr in r.get("guiding_question_responses", [])
            ]
        })
    prompt = load_prompt("report_prompt.txt").format(
        student_name=session_data["student_name"],
        iteration=session_data["iteration"],
        questions_json=json.dumps(summaries, indent=2)
    )
    msg = client.messages.create(model=CLAUDE_MODEL, max_tokens=4096,
                                  messages=[{"role": "user", "content": prompt}])
    return _parse_json(msg.content[0].text)

def generate_study_guide(report: dict, test_data: dict) -> dict:
    prompt = load_prompt("study_guide_prompt.txt").format(
        student_name=report["student_name"],
        weak_topics=", ".join(report["weak_topics"]),
        weaknesses_summary=report["weaknesses_summary"]
    )
    msg = client.messages.create(model=CLAUDE_MODEL, max_tokens=8192,
                                  messages=[{"role": "user", "content": prompt}])
    return _parse_json(msg.content[0].text)

def generate_adaptive_test(student_name: str, iteration: int, weak_topics: list,
                            previous_scores: list, session_dates: list,
                            total_questions: int = 15) -> dict:
    prompt = load_prompt("test_gen_prompt.txt").format(
        student_name=student_name,
        student_name_lower=student_name.lower(),
        iteration=iteration,
        prev_iteration=iteration - 1,
        weak_topics=", ".join(weak_topics),
        weak_topics_json=json.dumps(weak_topics),
        previous_scores=", ".join(str(s) for s in previous_scores),
        session_dates=", ".join(session_dates),
        total_questions=total_questions
    )
    msg = client.messages.create(model=CLAUDE_MODEL, max_tokens=8192,
                                  messages=[{"role": "user", "content": prompt}])
    return _parse_json(msg.content[0].text)

async def stream_chat(messages: list[dict], system_prompt: str):
    """Async generator yielding text chunks for SSE streaming."""
    with client.messages.stream(
        model=CLAUDE_CHAT_MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=messages
    ) as stream:
        for text in stream.text_stream:
            yield text
```

### Step 3.4 — backend/routers/ai.py

```python
import re, json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pathlib import Path
from config import STUDENTS_DIR, TESTS_DIR
from services.claude_service import (
    load_prompt, generate_report, generate_study_guide,
    generate_adaptive_test, stream_chat
)

router = APIRouter()

def get_student_dir(name: str) -> Path:
    safe = re.sub(r'[^\w]', '_', name.lower().strip())
    return STUDENTS_DIR / f"{safe}_data"

@router.post("/{student_name}/{session_id}/report")
async def create_report(student_name: str, session_id: str):
    student_dir   = get_student_dir(student_name)
    session_dir   = student_dir / session_id
    responses_path = session_dir / "responses.json"
    if not responses_path.exists():
        raise HTTPException(404, "Session responses not found")
    session_data = json.loads(responses_path.read_text())
    meta         = json.loads((session_dir / "metadata.json").read_text())
    test_data    = json.loads((TESTS_DIR / f"{meta['test_id']}.json").read_text())
    report       = generate_report(session_data, test_data)
    report.update({
        "report_id": f"report_{meta['iteration']}",
        "student_name": student_name,
        "iteration": meta["iteration"],
        "generated_at": datetime.now(timezone.utc).isoformat()
    })
    (student_dir / f"report_{meta['iteration']}.json").write_text(json.dumps(report, indent=2))
    return report

@router.post("/{student_name}/{session_id}/study-guide")
async def create_study_guide(student_name: str, session_id: str):
    student_dir = get_student_dir(student_name)
    meta        = json.loads((student_dir / session_id / "metadata.json").read_text())
    iteration   = meta["iteration"]
    report_path = student_dir / f"report_{iteration}.json"
    if not report_path.exists():
        raise HTTPException(400, "Generate report before study guide")
    report    = json.loads(report_path.read_text())
    test_data = json.loads((TESTS_DIR / f"{meta['test_id']}.json").read_text())
    guide     = generate_study_guide(report, test_data)
    guide.update({
        "study_guide_id": f"study_guide_{iteration}",
        "student_name": student_name,
        "iteration": iteration,
        "weak_topics": report["weak_topics"],
        "generated_at": datetime.now(timezone.utc).isoformat()
    })
    (student_dir / f"study_guide_{iteration}.json").write_text(json.dumps(guide, indent=2))
    return guide

class ChatRequest(BaseModel):
    student_name: str
    messages: list[dict]
    weak_topics: list[str]
    weaknesses_summary: str

@router.post("/chat")
async def chat(req: ChatRequest):
    system_prompt = load_prompt("chat_system_prompt.txt").format(
        student_name=req.student_name,
        weak_topics=", ".join(req.weak_topics),
        weaknesses_summary=req.weaknesses_summary
    )
    async def generate():
        async for chunk in stream_chat(req.messages, system_prompt):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")

class AdaptiveTestRequest(BaseModel):
    student_name: str
    total_questions: int = 15

@router.post("/{student_name}/generate-test")
async def create_adaptive_test(student_name: str, req: AdaptiveTestRequest):
    student_dir = get_student_dir(student_name)
    all_reports = [json.loads(p.read_text())
                   for p in sorted(student_dir.glob("report_*.json"))]
    if not all_reports:
        raise HTTPException(400, "No session history found")
    topic_count: dict[str, int] = {}
    for r in all_reports:
        for t in r.get("weak_topics", []):
            topic_count[t] = topic_count.get(t, 0) + 1
    persistent_weak = sorted(topic_count, key=lambda t: topic_count[t], reverse=True)
    iteration       = len(all_reports) + 1
    new_test        = generate_adaptive_test(
        student_name=student_name,
        iteration=iteration,
        weak_topics=persistent_weak[:5],
        previous_scores=[r["overall_score_percent"] for r in all_reports],
        session_dates=[r["generated_at"][:10] for r in all_reports],
        total_questions=req.total_questions
    )
    filename = f"{student_name.lower()}_iteration_{iteration}.json"
    (TESTS_DIR / filename).write_text(json.dumps(new_test, indent=2))
    return {"test_id": new_test["test_id"], "test_filename": filename,
            "iteration": iteration, "weak_topics_targeted": persistent_weak[:5]}
```

Register in main.py:
```python
from routers import audio, ai
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
app.include_router(ai.router,    prefix="/api/ai",    tags=["ai"])
```

### Step 3.5 — Study Module Frontend

StudyModule.tsx manages 4 tabs (render after both report + study guide are loaded):
  Tab 1 "Report"     -> ReportView: score bar, topic analysis table, strengths/weaknesses, action steps
  Tab 2 "Reading"    -> Reading summaries per weak topic, expandable sections
  Tab 3 "Practice"   -> Flashcards.tsx (flip card on click) then MiniQuiz.tsx (MC with immediate feedback)
  Tab 4 "Ask Claude" -> ChatInterface.tsx (streaming SSE)

On mount sequence:
  1. Show spinner: "Generating your performance report..."
  2. POST /api/ai/{name}/{session_id}/report  (~5-15s)
  3. Show spinner: "Generating study materials..."
  4. POST /api/ai/{name}/{session_id}/study-guide  (~10-20s)
  5. Render all 4 tabs

frontend/src/hooks/useStreamingChat.ts:

```typescript
import { useState } from 'react'

interface ChatMessage { role: 'user' | 'assistant'; content: string }

export function useStreamingChat(
  studentName: string, weakTopics: string[], weaknessesSummary: string
) {
  const [messages, setMessages]     = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = async (userText: string) => {
    const newMessages = [...messages, { role: 'user' as const, content: userText }]
    setMessages([...newMessages, { role: 'assistant', content: '' }])
    setIsStreaming(true)
    const res = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: studentName, messages: newMessages,
        weak_topics: weakTopics, weaknesses_summary: weaknessesSummary
      })
    })
    const reader  = res.body!.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      for (const line of decoder.decode(value).split('\n')) {
        if (line.startsWith('data: ') && !line.includes('[DONE]')) {
          const { text } = JSON.parse(line.slice(6))
          setMessages(m => {
            const updated = [...m]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: updated[updated.length - 1].content + text
            }
            return updated
          })
        }
      }
    }
    setIsStreaming(false)
  }

  return { messages, sendMessage, isStreaming }
}
```

After the student completes all 4 tabs (or at any point), show:
  "Ready for your next test?" [Take Adaptive Test] button

Clicking it:
  1. Call PATCH /api/sessions/{name}/{session_id}/mark-study-complete
  2. Show loading state: "Claude is building your personalized test... (~20 seconds)"
  3. POST /api/ai/{name}/generate-test
  4. On success: start TestRunner with the returned test_id

---

## Phase 4: Iteration Loop Completion

### Step 4.1 — History-Aware Welcome Screen

NameEntry.tsx on submit:
  1. Call GET /api/sessions/{name}/history
  2. If sessions = [] -> go directly to test with ap_csa_test_1
  3. If sessions exist:
     - Find latest session metadata
     - Find latest report (if exists)
     - Display:
         "Welcome back, {name}!
          Iteration {N} complete. Last score: {score}%.
          Persistent weak areas: {topics}
          [Continue Study Module]  <- only if study_completed = false
          [Take Next Test]          <- only if study_completed = true"
     - "Continue Study Module" navigates to StudyModule with existing session data
     - "Take Next Test" calls POST /api/ai/{name}/generate-test then starts TestRunner

### Step 4.2 — App State Machine (Phase 4)

```typescript
type AppView = 'name_entry' | 'test' | 'study' | 'generating_test'

// In App.tsx, render a header when not on name_entry:
// "Iteration {N} — AP CSA {Diagnostic | Adaptive} Test"
```

Show iteration number prominently in the UI so the student knows their progress.

### Step 4.3 — Live Java Tracer (Optional Enhancement)

For generated code_trace questions, execution_trace will be null.
JavaVisualizer already handles this gracefully (shows "Step-through not available").

If you want live tracing for generated questions, implement either:

Option A — Claude-generated traces (simpler):
  After generate_adaptive_test() returns, loop over questions where type == "code_trace"
  and code_block is not null. For each, make a separate Claude API call to generate
  the execution_trace using the prompt from Step 2.2. Attach to the question before saving.
  This adds ~5s per code_trace question but requires no additional infrastructure.

Option B — JDI-based live tracer (complex):
  java-tracer/Tracer.java: Use the Java Debug Interface (com.sun.jdi) to attach to a
  forked JVM running the target code and capture each bytecode step.
  Compile: javac --add-modules jdk.jdi -d java-tracer/out java-tracer/*.java
  Build:   jar cf java-tracer/out/tracer.jar -C java-tracer/out .
  Run via backend/routers/visualizer.py subprocess call (10s timeout, no file I/O allowed).
  This provides real-time tracing for any code but is significantly more complex to implement.

Recommendation: implement Option A first. Add Option B only if needed for generated tests.

---

## Take-Home Assignments

Since April 2026 the app supports long-form take-home coding assignments served
both (a) in-browser via a Monaco-based IDE and (b) as standalone `.java` files
the student can run locally in IntelliJ/VS Code.

### Directory layout (per assignment)

```
data/students/{name}_data/take_home_session_{N}/
├── README.md                  <- student-facing instructions
├── manifest.json              <- question list + metadata (frontend reads this)
├── Q1/
│   ├── Q1.java                <- base question + starter code + answer-key comment
│   ├── Q1A.java               <- Variant A (self-contained, embedded test runner)
│   ├── Q1B.java               <- Variant B (self-contained, embedded test runner)
│   ├── Q1A.json               <- Variant A metadata (test cases + summaries) — web IDE
│   └── Q1B.json               <- Variant B metadata — web IDE
├── Q2/ ... Q15/
├── _reference/                <- hand-crafted Java style exemplars
└── _student_journey_report/   <- Playwright test screenshots + findings.json
```

### Variant JSON schema

Each `Q{N}{A,B}.json` has:
- `id`, `parent_question`, `mutation_description`, `concept_tested`, `difficulty`, `topic_tags`
- `starter_modification` — step-by-step edits the student must make
- `test_cases[]` — each with `id`, `description`, `method_call`, `method_type`
  (`"value_return"` or `"void_print"` — tells the runner whether to wrap in
  `System.out.println(...)` or call bare), `expected_output`, `what_it_tests`, `wrong_means`
- `summary` — `what_this_tests`, `why`, `concept_background` (shown in Info panel)
- `metadata` — `started_at`, `completed_at`, `total_time_ms`, `run_attempts`, `test_results`

### Combined `Q{N}{A,B}.java` format

Generated by `scripts/combine_variants_into_java.py`:
- Top docstring: task, step-by-step, concept, how-to-use
- The starter method (renamed into class `Q{N}{A,B}`) — student modifies this
- `main()` = test runner:
  - Per test case: captures stdout into `ByteArrayOutputStream`, compares to
    expected output with trailing-whitespace normalized (`replaceAll("\\s+$","")`)
  - Prints `✓ PASS` / `✗ FAIL` with escaped expected/actual + "wrong means" diagnostic
  - Summary at end: `Results: N passed, M failed`

### Frontend route

`http://localhost:5173/?takehome={student_dir}/{assignment_dir}` mounts
`TakeHomeRunner` (`frontend/src/components/TakeHome/TakeHomeRunner.tsx`) which:
- Loads `manifest.json` + the current question's `.java` + active variant `.json`
  via `GET /api/takehome/...`
- Monaco editor (dark theme, glyph margin for breakpoints)
- Toolbar: `[▶ Run Code] [🧪 Tests] [🔬 Visualize] [📖 Info] [↺ Reset]`
  - Tests → POST `/api/execute/` per test case, compares stdout, renders PASS/FAIL
  - Visualize → embeds `cscircles.cemc.uwaterloo.ca/java_visualize` iframe with
    the student's current code (URL-encoded)
  - Info → renders `summary.{what_this_tests, why, concept_background, concept_tested}`

### Generator scripts

- `scripts/generate_session6_takehome.py` — Claude-driven generator. Reads
  student reports from prior sessions + question bank + reference exemplars,
  produces 15 questions with 2 variants each. Compile-validates every starter
  with `javac` and retries once on failure.
- `scripts/combine_variants_into_java.py` — fuses base Java + variant JSON
  into self-contained runnable Java files (one per variant).
- `scripts/test_takehome_as_student.mjs` — Playwright student-journey test.
  Verifies toolbar, editor, test runner, visualizer iframe, info panel, and
  full question navigation. Writes screenshots + findings.json to the
  assignment directory's `_student_journey_report/`.

---

## Key Implementation Notes

### 1. .docx Conversion — Inspect First, Always
Never implement extract_questions() without first running --inspect and reading its output.
The document structure cannot be predicted from the outside. Common failure modes:
  - Code blocks use inline Courier New font, not a named paragraph style
  - Question numbers restart across document sections
  - Answer key may be in a separate section of the tutor guide, not inline
  - Guiding questions may be in a table rather than numbered paragraphs
Detect code blocks via: any(run.font.name == 'Courier New' for run in para.runs)

### 2. Monaco Line Highlighting
The deltaDecorations() pattern:
  - Store the editor instance in useRef (not useState) to avoid re-renders
  - Store the previous decoration IDs in another useRef
  - In useEffect([stepIndex]), pass previous IDs as first arg to deltaDecorations
    to clear old highlights before applying new ones
  - Failure to pass previous IDs causes decorations to pile up across steps

### 3. Vosk Model Path
Model() must receive the path to the inner directory containing the am/ subfolder.
  Correct: Model("data/vosk-model/vosk-model-small-en-us-0.15")
  Wrong:   Model("data/vosk-model/")
Model loading takes ~2 seconds; lazy-load on first transcription request using the _model global.
Test the path standalone before integrating: python3 -c "from vosk import Model; Model('...')"

### 4. WebM to WAV Conversion
Browser MediaRecorder produces WebM/Opus by default. Vosk requires 16kHz 16-bit mono PCM WAV.
pydub handles the conversion but requires ffmpeg on the system PATH.
If ffmpeg is missing, pydub raises a cryptic error. Verify with: ffmpeg -version
Conversion line: audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

### 5. Claude JSON Output Reliability
Claude occasionally wraps JSON in markdown code fences (```json ... ```).
The _parse_json() helper strips these. Always include in prompts the instruction:
"Return only raw JSON — no markdown, no code fences, no explanation text."
Always validate the parsed result has the expected top-level keys before using it.

### 6. Student Name Sanitization
Use re.sub(r'[^\w]', '_', name.lower().strip()) in EVERY function that constructs a student
directory path. Inconsistent sanitization between endpoints will cause path mismatches.
Define a single get_student_dir(name) helper and import it everywhere rather than
re-implementing the sanitization logic in multiple places.

### 7. Null execution_trace Handling
JavaVisualizer must render without crashing when trace is null.
The conditional `trace && currentStep ? <visualizer> : <fallback>` handles this.
Do not pass trace=null to JavaVisualizer without a null guard.

### 8. Streaming Chat — Async Generator
stream_chat is an async generator (uses `yield`). The FastAPI route must be async.
The generator passed to StreamingResponse must also be async (`async def generate()`).
Do not use sync generators with StreamingResponse in FastAPI.

### 9. Claude API Model Names (use exact strings)
  Full capability:  claude-opus-4-6    (use for reports, study guides, test generation)
  Cost-efficient:   claude-sonnet-4-6  (use for streaming chat to reduce latency and cost)
Do not abbreviate or guess model IDs. Set them in config.py as CLAUDE_MODEL and CLAUDE_CHAT_MODEL.

### 10. Adaptive Test Validation
After generate_adaptive_test() returns parsed JSON, validate before saving to disk:
  - "questions" key exists and is a non-empty list
  - Each question has: id, type, answer_key, guiding_questions
  - No answer_key is null or empty
If validation fails, retry the Claude call once with the instruction to fix the schema issue.
If it fails again, raise an HTTPException with a clear message.

---

## Dependencies

### backend/requirements.txt
```
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9
python-dotenv==1.0.1
anthropic==0.28.0
vosk==0.3.45
python-docx==1.1.2
pydantic==2.7.1
aiofiles==23.2.1
httpx==0.27.0
pydub==0.25.1
```

System (not pip):
  ffmpeg    — audio format conversion (download from ffmpeg.org or brew install ffmpeg)
  OpenJDK 26 — already present in this project (used for java-tracer in Phase 4)

### frontend/package.json
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "@monaco-editor/react": "^4.6.0",
    "monaco-editor": "^0.50.0",
    "axios": "^1.7.2",
    "zustand": "^4.5.2",
    "react-router-dom": "^6.24.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.4.5",
    "vite": "^5.3.1"
  }
}
```

---

## Build Checklists

### Phase 1 Checklist — Core Test Flow
- [ ] Install Node 20 via nvm
- [ ] Install Python 3.11 via pyenv; run pyenv local 3.11.9 from project root
- [ ] Create backend/venv; pip install -r backend/requirements.txt
- [ ] Create directory structure: backend/, frontend/, data/tests/, data/students/, scripts/
- [ ] Run: python scripts/convert_docx.py --inspect   (read ALL output before proceeding)
- [ ] Implement extract_questions() based on actual document structure
- [ ] Assign topic_tags via Claude API call per question
- [ ] Run full conversion; inspect data/tests/ap_csa_test_1.json manually
- [ ] Run scripts/validate_json.py to confirm schema compliance
- [ ] Implement config.py, main.py, routers/tests.py, routers/sessions.py, models/session.py
- [ ] Test API with curl: GET /api/health, GET /api/tests/, POST /api/sessions/start
- [ ] Initialize React app with Vite; npm install dependencies
- [ ] Implement NameEntry, TestRunner, QuestionCard, MultipleChoice, FreeResponse
- [ ] End-to-end test: name entry -> take test -> verify responses.json saved to disk

### Phase 2 Checklist — Java Visualizer + Audio
- [ ] npm install @monaco-editor/react monaco-editor
- [ ] Implement JavaVisualizer.tsx with Monaco + deltaDecorations line highlighting
- [ ] Implement VariablePanel.tsx (stack frames bottom-to-top)
- [ ] Wire JavaVisualizer into CodeTrace type in QuestionCard
- [ ] Generate execution_trace JSON for all code_trace questions (via Claude or manual)
- [ ] Update ap_csa_test_1.json with traces; verify step-through works in browser
- [ ] Download Vosk model; extract to data/vosk-model/vosk-model-small-en-us-0.15/
- [ ] Install ffmpeg system-wide; verify with ffmpeg -version
- [ ] Implement vosk_transcriber.py and audio.py; register audio router in main.py
- [ ] Implement AudioCapture.tsx; wire into QuestionCard for each guiding question
- [ ] End-to-end audio test: record -> upload -> see transcript in UI -> verify .wav saved to disk

### Phase 3 Checklist — Claude AI Layer
- [ ] Create backend/.env with ANTHROPIC_API_KEY; add .env to .gitignore
- [ ] Write all 4 prompt template files in backend/prompts/
- [ ] Implement claude_service.py (generate_report, generate_study_guide, generate_adaptive_test, stream_chat, _parse_json)
- [ ] Implement ai.py router; register in main.py
- [ ] Implement ReportView.tsx, Flashcards.tsx, MiniQuiz.tsx
- [ ] Implement ChatInterface.tsx and useStreamingChat.ts hook
- [ ] Implement StudyModule.tsx with 4-tab navigation
- [ ] End-to-end test: complete test -> report generates -> study guide generates -> streaming chat works -> study guide files saved to disk

### Phase 4 Checklist — Iteration Loop
- [ ] Implement PATCH /api/sessions/{name}/{id}/mark-study-complete in sessions.py
- [ ] Implement POST /api/ai/{name}/generate-test (already in ai.py above)
- [ ] Implement history-aware welcome logic in NameEntry.tsx
- [ ] Wire "Take Adaptive Test" button in StudyModule with loading state
- [ ] Add 'generating_test' view to App.tsx state machine
- [ ] Add iteration number to UI header
- [ ] Full loop test: session 1 -> study module -> generate test -> session 2 -> verify data/students/{name}_data/ has 2 sessions, 2 reports, 2 study guides

---

## Files to Leave Untouched

- src/Main.java                — existing educational example demonstrating pass-by-value
- APCompSci.iml, .idea/        — IntelliJ project configuration
- bella_ap_csa_test.docx       — source test document (read-only input to conversion script)
- bella_ap_calcbc_test.docx    — not used in this build (AP Calc BC scope deferred)
- bella_tutor_guide.docx       — source guiding questions (read-only input to conversion script)

---

## Phase 5: Multi-Agent Development Pipeline

> Design: `MultiAgentDesign.md` | Implementation plan: `MultiAgentImplementation.md`

### Overview

A Python orchestrator pipeline that runs: Planning → [Code — human/Claude Code step] → Testing → Review → Docs. Each agent is an Anthropic API call with a scoped system prompt loaded from `.claude/rules/`. Shared state lives in `HANDOFF_STATE.json` (the "blackboard").

### Files Created

| File | Role |
|------|------|
| `backend/agents/__init__.py` | Package marker |
| `backend/agents/handoff.py` | HandoffState Pydantic schema + read/write/delete |
| `backend/agents/transfers.py` | Transfer tool definitions (Claude tool schemas) |
| `backend/agents/config.py` | Agent system prompts loaded from `.claude/rules/` |
| `backend/agents/planning.py` | Planning Agent — reads blackboard, scopes one task |
| `backend/agents/testing.py` | Testing Agent — 5-step validation sequence |
| `backend/agents/review.py` | Review Agent — fixed security/schema/regression checklist |
| `backend/agents/docs.py` | Documentation Agent — updates blackboard files |
| `backend/orchestrator.py` | Pipeline runner with max-3 retry guard |

### Usage

```bash
# Start a new session (runs Planning Agent, then pauses for Code Agent)
PYTHONPATH=backend python backend/orchestrator.py "Add /api/report endpoint"

# Resume after Code Agent (human/Claude Code) completes
PYTHONPATH=backend python backend/orchestrator.py --resume
```

### HANDOFF_STATE.json Lifecycle

```
Planning creates it
  → Code Agent reads scoped_task (human step — Claude Code)
  → Testing appends testing result
  → Review appends review result
  → Docs archives key parts to PROGRESS.md
  → File deleted at session end
```

### Retry Guard

Testing and Review loops are capped at `MAX_RETRIES = 3` in `backend/orchestrator.py`. On hitting the limit, the pipeline exits with code 1 and preserves `HANDOFF_STATE.json` for debugging.

### Agent Tool Restrictions

| Agent | Can write | Cannot write |
|-------|-----------|--------------|
| Planning | TASKS.md, PROGRESS.md | Source files, data/ |
| Code | backend/, frontend/src/ | data/students/, .env |
| Testing | (none — validates only) | All files |
| Review | (none — read-only) | All files |
| Docs | BuildGuide.md, PROGRESS.md, DECISIONS.md, TASKS.md, PARKING_LOT.md | Source files, data/ |
