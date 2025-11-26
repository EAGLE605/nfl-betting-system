"""
Automated Database Backup System

Creates timestamped backups of all SQLite databases.
Supports:
- Full backups (copy entire database)
- Incremental backups (WAL checkpointing)
- Automatic cleanup of old backups
- Integrity verification

BEGINNER GUIDE:
---------------
Why backups matter:
- SQLite is a single file - one corruption = total data loss
- Backups let you recover from accidental deletions
- Essential for any production system

How to use:
    python scripts/backup_database.py              # Full backup
    python scripts/backup_database.py --verify     # Backup + verify integrity
    python scripts/backup_database.py --cleanup 7  # Keep only 7 days of backups

Schedule with cron (Linux/Mac) or Task Scheduler (Windows):
    0 3 * * * python /path/to/backup_database.py  # Daily at 3 AM
"""

import argparse
import hashlib
import logging
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/backup.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Databases to backup
DATABASES = [
    "data/adaptive_learning.db",
    "data/odds_history.db",
]

# Additional data files to backup
DATA_FILES = [
    "data/strategies/registry.json",
    "data/edges_database.json",
    "config/config.yaml",
]

# Backup directory
BACKUP_DIR = Path("backups")

# Default retention period (days)
DEFAULT_RETENTION_DAYS = 30


# =============================================================================
# BACKUP FUNCTIONS
# =============================================================================


def get_file_hash(file_path: Path) -> str:
    """
    Calculate MD5 hash of a file.

    Used to verify backup integrity.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def verify_database_integrity(db_path: Path) -> bool:
    """
    Verify SQLite database integrity.

    Returns:
        True if database is healthy, False otherwise
    """
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        conn.close()
        return result == "ok"
    except Exception as e:
        logger.error(f"Integrity check failed for {db_path}: {e}")
        return False


def backup_database(db_path: Path, backup_dir: Path, timestamp: str) -> dict:
    """
    Create a backup of a SQLite database.

    Uses SQLite's backup API for consistency (handles active writes).

    Args:
        db_path: Path to the database file
        backup_dir: Directory to store backups
        timestamp: Timestamp string for backup filename

    Returns:
        Dict with backup info (path, size, hash, success)
    """
    result = {
        "source": str(db_path),
        "success": False,
        "backup_path": None,
        "size_bytes": 0,
        "hash": None,
        "error": None,
    }

    if not db_path.exists():
        result["error"] = f"Database not found: {db_path}"
        logger.warning(result["error"])
        return result

    try:
        # Create backup filename
        db_name = db_path.stem
        backup_filename = f"{db_name}_{timestamp}.db"
        backup_path = backup_dir / backup_filename

        # Use SQLite backup API (safer than file copy for active databases)
        source_conn = sqlite3.connect(str(db_path))
        backup_conn = sqlite3.connect(str(backup_path))

        with backup_conn:
            source_conn.backup(backup_conn)

        source_conn.close()
        backup_conn.close()

        # Get backup info
        result["backup_path"] = str(backup_path)
        result["size_bytes"] = backup_path.stat().st_size
        result["hash"] = get_file_hash(backup_path)
        result["success"] = True

        logger.info(
            f"Backed up {db_path.name} -> {backup_filename} ({result['size_bytes']:,} bytes)"
        )

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Backup failed for {db_path}: {e}")

    return result


def backup_file(file_path: Path, backup_dir: Path, timestamp: str) -> dict:
    """
    Backup a regular file (JSON, YAML, etc.).

    Args:
        file_path: Path to the file
        backup_dir: Directory to store backups
        timestamp: Timestamp string for backup filename

    Returns:
        Dict with backup info
    """
    result = {
        "source": str(file_path),
        "success": False,
        "backup_path": None,
        "size_bytes": 0,
        "hash": None,
        "error": None,
    }

    if not file_path.exists():
        result["error"] = f"File not found: {file_path}"
        logger.warning(result["error"])
        return result

    try:
        # Create backup filename
        backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_filename

        # Copy file
        shutil.copy2(file_path, backup_path)

        # Get backup info
        result["backup_path"] = str(backup_path)
        result["size_bytes"] = backup_path.stat().st_size
        result["hash"] = get_file_hash(backup_path)
        result["success"] = True

        logger.info(
            f"Backed up {file_path.name} -> {backup_filename} ({result['size_bytes']:,} bytes)"
        )

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Backup failed for {file_path}: {e}")

    return result


def cleanup_old_backups(backup_dir: Path, retention_days: int) -> int:
    """
    Delete backups older than retention period.

    Args:
        backup_dir: Directory containing backups
        retention_days: Number of days to keep backups

    Returns:
        Number of files deleted
    """
    if not backup_dir.exists():
        return 0

    cutoff_date = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0

    for backup_file in backup_dir.iterdir():
        if backup_file.is_file():
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_time < cutoff_date:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup_file.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {backup_file.name}: {e}")

    return deleted_count


def create_backup_manifest(backup_dir: Path, results: list, timestamp: str) -> Path:
    """
    Create a manifest file listing all backups.

    Args:
        backup_dir: Directory containing backups
        results: List of backup results
        timestamp: Backup timestamp

    Returns:
        Path to manifest file
    """
    import json

    manifest = {
        "timestamp": timestamp,
        "created_at": datetime.now().isoformat(),
        "backups": results,
        "total_size_bytes": sum(r.get("size_bytes", 0) for r in results),
        "success_count": sum(1 for r in results if r.get("success")),
        "failure_count": sum(1 for r in results if not r.get("success")),
    }

    manifest_path = backup_dir / f"manifest_{timestamp}.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest_path


def run_backup(verify: bool = False, cleanup_days: int = None) -> dict:
    """
    Run full backup of all databases and data files.

    Args:
        verify: Whether to verify database integrity after backup
        cleanup_days: If set, delete backups older than this many days

    Returns:
        Summary of backup operation
    """
    print("\n" + "=" * 60)
    print("DATABASE BACKUP SYSTEM")
    print("=" * 60 + "\n")

    # Create backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUP_DIR / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    logger.info(f"Starting backup to {backup_dir}")

    results = []

    # Backup databases
    print("\n[1/3] Backing up databases...")
    for db_path_str in DATABASES:
        db_path = Path(db_path_str)
        result = backup_database(db_path, backup_dir, timestamp)
        results.append(result)

        if verify and result["success"]:
            is_valid = verify_database_integrity(Path(result["backup_path"]))
            result["integrity_verified"] = is_valid
            if is_valid:
                logger.info(f"  [OK] Integrity verified: {db_path.name}")
            else:
                logger.error(f"  [FAIL] Integrity check failed: {db_path.name}")

    # Backup data files
    print("\n[2/3] Backing up data files...")
    for file_path_str in DATA_FILES:
        file_path = Path(file_path_str)
        result = backup_file(file_path, backup_dir, timestamp)
        results.append(result)

    # Create manifest
    manifest_path = create_backup_manifest(backup_dir, results, timestamp)
    logger.info(f"Created manifest: {manifest_path.name}")

    # Cleanup old backups
    if cleanup_days:
        print(f"\n[3/3] Cleaning up backups older than {cleanup_days} days...")
        deleted = cleanup_old_backups(BACKUP_DIR, cleanup_days)
        logger.info(f"Deleted {deleted} old backup files")
    else:
        print("\n[3/3] Skipping cleanup (use --cleanup N to enable)")

    # Summary
    success_count = sum(1 for r in results if r.get("success"))
    total_size = sum(r.get("size_bytes", 0) for r in results)

    summary = {
        "timestamp": timestamp,
        "backup_dir": str(backup_dir),
        "total_files": len(results),
        "successful": success_count,
        "failed": len(results) - success_count,
        "total_size_bytes": total_size,
        "manifest": str(manifest_path),
    }

    print("\n" + "=" * 60)
    print("BACKUP SUMMARY")
    print("=" * 60)
    print(f"  Timestamp: {timestamp}")
    print(f"  Location:  {backup_dir}")
    print(f"  Files:     {success_count}/{len(results)} successful")
    print(f"  Total:     {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
    print("=" * 60 + "\n")

    if success_count == len(results):
        logger.info("Backup completed successfully!")
    else:
        logger.warning(f"Backup completed with {len(results) - success_count} failures")

    return summary


def restore_backup(backup_dir: str, target_dir: str = None) -> bool:
    """
    Restore databases from a backup.

    Args:
        backup_dir: Path to backup directory (e.g., "backups/20251125_030000")
        target_dir: Optional target directory (default: original locations)

    Returns:
        True if restore successful
    """
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        logger.error(f"Backup directory not found: {backup_dir}")
        return False

    print(f"\nRestoring from: {backup_path}")

    # Find manifest
    manifests = list(backup_path.glob("manifest_*.json"))
    if not manifests:
        logger.error("No manifest found in backup directory")
        return False

    import json

    with open(manifests[0]) as f:
        manifest = json.load(f)

    restored = 0
    for backup_info in manifest["backups"]:
        if not backup_info.get("success"):
            continue

        backup_file = Path(backup_info["backup_path"])
        if not backup_file.exists():
            logger.warning(f"Backup file not found: {backup_file}")
            continue

        # Determine target path
        source_path = Path(backup_info["source"])
        if target_dir:
            target_path = Path(target_dir) / source_path.name
        else:
            target_path = source_path

        try:
            # Create target directory if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy backup to target
            shutil.copy2(backup_file, target_path)
            logger.info(f"Restored: {backup_file.name} -> {target_path}")
            restored += 1

        except Exception as e:
            logger.error(f"Failed to restore {backup_file.name}: {e}")

    print(f"\nRestored {restored} files")
    return restored > 0


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Database Backup System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backup_database.py                    # Full backup
  python backup_database.py --verify           # Backup + verify integrity
  python backup_database.py --cleanup 7        # Keep only 7 days of backups
  python backup_database.py --restore backups/20251125_030000
        """,
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify database integrity after backup",
    )

    parser.add_argument(
        "--cleanup",
        type=int,
        metavar="DAYS",
        help="Delete backups older than DAYS",
    )

    parser.add_argument(
        "--restore",
        type=str,
        metavar="BACKUP_DIR",
        help="Restore from backup directory",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups",
    )

    args = parser.parse_args()

    if args.list:
        # List available backups
        if not BACKUP_DIR.exists():
            print("No backups found")
            return

        backups = sorted(BACKUP_DIR.iterdir(), reverse=True)
        print(f"\nAvailable backups in {BACKUP_DIR}:\n")
        for backup in backups:
            if backup.is_dir():
                size = sum(f.stat().st_size for f in backup.iterdir() if f.is_file())
                print(f"  {backup.name}  ({size:,} bytes)")
        print()

    elif args.restore:
        # Restore from backup
        restore_backup(args.restore)

    else:
        # Run backup
        run_backup(
            verify=args.verify,
            cleanup_days=args.cleanup or DEFAULT_RETENTION_DAYS,
        )


if __name__ == "__main__":
    main()
