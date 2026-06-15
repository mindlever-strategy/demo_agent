import json
import os
import shutil
from pathlib import Path

_SEED_DIR = Path(__file__).parent / "memory"
_IS_VERCEL = bool(os.getenv("VERCEL"))


def get_memory_dir() -> Path:
    if _IS_VERCEL:
        memory_dir = Path("/tmp/metric-demo-memory")
        memory_dir.mkdir(parents=True, exist_ok=True)
        _seed_memory_dir(memory_dir)
        return memory_dir
    return _SEED_DIR


def _seed_memory_dir(memory_dir: Path) -> None:
    for filename in ("users.json", "sessions.json", "traces.json"):
        dest = memory_dir / filename
        if dest.exists():
            continue
        src = _SEED_DIR / filename
        if src.exists():
            shutil.copy(src, dest)
        else:
            dest.write_text("[]", encoding="utf-8")


def load_json(filename: str):
    filepath = get_memory_dir() / filename
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_json(filename: str, data) -> None:
    filepath = get_memory_dir() / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
