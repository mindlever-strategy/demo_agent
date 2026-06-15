import importlib.util
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent / "backend"
backend_main_path = backend_dir / "main.py"

sys.path.insert(0, str(backend_dir))

spec = importlib.util.spec_from_file_location("metric_backend_main", backend_main_path)
backend_main = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(backend_main)

app = backend_main.app
