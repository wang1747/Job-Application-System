import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "backups"
DB_PATH = ROOT / "offerflow.db"


def main() -> None:
    BACKUP_DIR.mkdir(exist_ok=True)
    if not DB_PATH.exists():
        print("No SQLite database found.")
        return

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"offerflow-{timestamp}.db"
    shutil.copy2(DB_PATH, target)
    print(f"Backup created: {target}")


if __name__ == "__main__":
    main()
