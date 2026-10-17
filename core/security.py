"""
core/security.py
Security engine — hashing, validation, process monitoring, admin auth.
"""
 
import hashlib
import subprocess
import threading
import os
import sys
import hmac
from typing import Callable
 
import psutil
 
from core import database as db
 
 
def _norm(path: str) -> str:
    """Consistent path normalisation (mirrors database._norm)."""
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))
 
 
# ── Hashing ────────────────────────────────────────────────────────────────
 
def compute_sha256(filepath: str) -> str:
    """SHA-256 of a file, read in 64 KB chunks."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError) as e:
        raise RuntimeError(f"Cannot hash '{filepath}': {e}") from e
 
 
# ── Validation ─────────────────────────────────────────────────────────────
 
class ValidationResult:
    __slots__ = ("allowed", "status", "reason", "app_name", "path", "sha256")
 
    def __init__(self, allowed, status, reason, app_name="", path="", sha256=""):
        self.allowed  = allowed
        self.status   = status
        self.reason   = reason
        self.app_name = app_name
        self.path     = path
        self.sha256   = sha256
 
 
def validate_execution(filepath: str) -> ValidationResult:
    """
    Validate an execution attempt:
      1. Normalise path (handles case + slash differences on Windows).
      2. Check file exists.
      3. Look up in whitelist (normalised comparison).
      4. Verify SHA-256 matches stored hash.
    """
    filepath = _norm(filepath)
    app_name = os.path.basename(filepath)
 
    # ── File must exist ───────────────────────────────────────────────────
    if not os.path.isfile(filepath):
        db.add_log(app_name, filepath, "ERROR", reason="File not found.")
        return ValidationResult(False, "ERROR", "File not found.", app_name, filepath)
 
    # ── Compute live hash ─────────────────────────────────────────────────
    try:
        live_hash = compute_sha256(filepath)
    except RuntimeError as e:
        db.add_log(app_name, filepath, "ERROR", reason=str(e))
        return ValidationResult(False, "ERROR", str(e), app_name, filepath)
 
    # ── Whitelist lookup (uses normalised path internally) ────────────────
    entry = db.get_app_by_path(filepath)
 
    if entry is None:
        reason = "Not in whitelist."
        db.add_log(app_name, filepath, "BLOCKED", live_hash, reason)
        return ValidationResult(False, "BLOCKED", reason, app_name, filepath, live_hash)
 
    # ── Hash verification ─────────────────────────────────────────────────
    if not hmac.compare_digest(live_hash, entry["sha256"]):
        reason = (f"Hash mismatch! "
                  f"Stored: {entry['sha256'][:16]}…  Live: {live_hash[:16]}…")
        db.add_log(entry["name"], filepath, "HASH_MISMATCH", live_hash, reason)
        return ValidationResult(False, "HASH_MISMATCH", reason,
                                entry["name"], filepath, live_hash)
 
    # ── All good ──────────────────────────────────────────────────────────
    db.add_log(entry["name"], filepath, "ALLOWED", live_hash)
    return ValidationResult(True, "ALLOWED", "Application verified.",
                            entry["name"], filepath, live_hash)
 
 
def launch_application(filepath: str) -> tuple:
    """Validate then launch. Returns (success, message)."""
    result = validate_execution(filepath)
    if result.allowed:
        try:
            if sys.platform == "win32":
                os.startfile(filepath)
            else:
                subprocess.Popen(["xdg-open", filepath])
            return True, f"Launched: {result.app_name}"
        except Exception as e:
            return False, f"Launch failed: {e}"
    return False, f"Blocked — {result.reason}"
 
 
# ── Background Process Monitor ─────────────────────────────────────────────
 
class ProcessMonitor(threading.Thread):
    """Daemon thread that scans running processes every N seconds."""
 
    def __init__(self, on_violation: Callable, poll_interval: float = 5.0):
        super().__init__(daemon=True, name="ProcessMonitor")
        self._stop_event   = threading.Event()
        self._on_violation = on_violation
        self._poll_interval = poll_interval
        self._known_pids: set = set()
 
    def run(self):
        while not self._stop_event.is_set():
            try:
                self._scan()
            except Exception:
                pass
            self._stop_event.wait(self._poll_interval)
 
    def _scan(self):
        current_pids = set()
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                pid  = proc.info["pid"]
                name = proc.info["name"] or ""
                exe  = proc.info["exe"]
                if not exe:
                    continue
                current_pids.add(pid)
                if pid in self._known_pids:
                    continue
                exe_norm = _norm(exe)
                if self._is_system_path(exe_norm):
                    continue
                entry = db.get_app_by_path(exe_norm)
                if entry is None:
                    db.add_log(name, exe_norm, "BLOCKED",
                               reason="Detected by monitor — not whitelisted.")
                    self._on_violation(name, exe_norm, "Not in whitelist.")
                else:
                    try:
                        live_hash = compute_sha256(exe_norm)
                        if not hmac.compare_digest(live_hash, entry["sha256"]):
                            db.add_log(name, exe_norm, "HASH_MISMATCH", live_hash,
                                       reason="Monitor: hash mismatch.")
                            self._on_violation(name, exe_norm, "Hash mismatch!")
                    except RuntimeError:
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        self._known_pids = current_pids
 
    @staticmethod
    def _is_system_path(path: str) -> bool:
        lp = path.lower()
        skips = [r"c:\windows", r"c:\program files\windowsapps",
                 "/usr/", "/lib/", "/bin/", "/sbin/"]
        return any(lp.startswith(s) for s in skips)
 
    def stop(self):
        self._stop_event.set()
 
 
# ── Admin Auth ─────────────────────────────────────────────────────────────
 
def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
 
def set_admin_password(password: str) -> None:
    db.set_admin_password(_hash_password(password))
 
def verify_admin_password(password: str) -> bool:
    stored = db.get_admin_password_hash()
    if stored is None:
        return True
    return hmac.compare_digest(_hash_password(password), stored)
 
def admin_password_is_set() -> bool:
    return db.get_admin_password_hash() is not None