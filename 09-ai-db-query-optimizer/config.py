"""Configuration — DB connection, thresholds, Ollama settings."""
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "demo_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", 180))

SLOW_QUERY_THRESHOLD_MS = float(os.getenv("SLOW_QUERY_THRESHOLD_MS", 500))
N_PLUS_ONE_THRESHOLD = int(os.getenv("N_PLUS_ONE_THRESHOLD", 10))
AVG_DEV_HOURLY_RATE = float(os.getenv("AVG_DEV_HOURLY_RATE", 75))
DAILY_EXECUTIONS_DEFAULT = int(os.getenv("DAILY_EXECUTIONS_DEFAULT", 1000))
