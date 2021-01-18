from pathlib import Path


def get_cache_dir():
    cache_dir = Path.home() / "gluonts-run-tool"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


CACHE_DIR = get_cache_dir()
