import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

import main as backend_main  # noqa: E402

app = backend_main.app
