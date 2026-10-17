"""
core/exporter.py
CSV export helpers for logs.
"""

import csv
import os
from datetime import datetime
from core import database as db


def export_logs_csv(filepath: str, status_filter: str = "ALL") -> tuple[bool, str]:
    """
    Export the logs table to a CSV file.
    Returns (success, message).
    """
    try:
        rows = db.get_logs(status_filter, limit=100_000)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "App Name", "Path", "SHA-256", "Status", "Reason", "Timestamp"])
            for row in rows:
                writer.writerow([
                    row["id"],
                    row["app_name"],
                    row["path"],
                    row["sha256"] or "",
                    row["status"],
                    row["reason"] or "",
                    row["timestamp"],
                ])
        return True, f"Exported {len(rows)} records to:\n{filepath}"
    except Exception as e:
        return False, f"Export failed: {e}"


def export_whitelist_csv(filepath: str) -> tuple[bool, str]:
    """Export the whitelist to CSV."""
    try:
        rows = db.get_all_apps()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Path", "SHA-256", "Added On", "Enabled"])
            for row in rows:
                writer.writerow([
                    row["id"], row["name"], row["path"],
                    row["sha256"], row["added_on"], "Yes" if row["enabled"] else "No"
                ])
        return True, f"Exported {len(rows)} entries to:\n{filepath}"
    except Exception as e:
        return False, f"Export failed: {e}"
