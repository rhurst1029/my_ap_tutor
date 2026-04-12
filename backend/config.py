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
