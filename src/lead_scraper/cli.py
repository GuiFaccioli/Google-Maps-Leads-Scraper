from __future__ import annotations

import argparse

from lead_scraper.config import load_config
from lead_scraper.db import ensure_database


def init_db_command() -> None:
    config = load_config()
    ensure_database(config.database_path)
    print(f"Database initialized at: {config.database_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Google Maps leads scraper")
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Create the SQLite database and schema",
    )
    args = parser.parse_args()

    if args.init_db:
        init_db_command()


if __name__ == "__main__":
    main()

