import sys
from pathlib import Path

# Ensure project root is on sys.path so tests can import modules like transcribe_summary
PROJECT_ROOT = Path(__file__).resolve().parent.parent
project_str = str(PROJECT_ROOT)
if project_str not in sys.path:
    sys.path.insert(0, project_str)


