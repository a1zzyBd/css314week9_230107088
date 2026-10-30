from pathlib import Path

STUDENT_ID = "230107088"
ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
