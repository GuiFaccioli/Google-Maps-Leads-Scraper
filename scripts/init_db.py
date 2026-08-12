from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lead_scraper.config import load_config
from lead_scraper.db import ensure_database


def main() -> None:
    config = load_config()
    ensure_database(config.database_path)
    print(f"Database initialized at: {config.database_path}")


if __name__ == "__main__":
    main()
