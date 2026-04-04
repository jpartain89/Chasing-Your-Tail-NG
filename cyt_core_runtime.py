"""Shared runtime and monitoring services for CLI and UI entry points."""

from __future__ import annotations

import glob
import logging
import os
import pathlib
import threading
import time
from dataclasses import dataclass
from typing import IO, Callable, List, Optional, Tuple

from secure_credentials import SecureCredentialManager, secure_config_loader
from secure_database import SecureKismetDB
from secure_ignore_loader import load_ignore_lists
from secure_main_logic import SecureCYTMonitor


logger = logging.getLogger(__name__)


@dataclass
class RuntimeContext:
    """Shared app context for secure config and credentials."""

    config: dict
    credential_manager: SecureCredentialManager


def load_runtime_context(config_path: str = "config.json") -> RuntimeContext:
    """Load secure configuration and credentials once for a runtime."""
    config, credential_manager = secure_config_loader(config_path)
    return RuntimeContext(config=config, credential_manager=credential_manager)


def ensure_runtime_directories(config: dict) -> None:
    """Ensure output/runtime directories exist."""
    paths = config.get("paths", {})
    # Directories that must exist before the runtime writes any output.
    dir_keys = [
        "log_dir",
        "reports_dir",
        "kml_dir",
        "surveillance_reports_dir",
        "analysis_logs_dir",
    ]
    for key in dir_keys:
        value = paths.get(key)
        if value:
            pathlib.Path(value).mkdir(parents=True, exist_ok=True)


def create_cyt_log(config: dict) -> Tuple[str, IO[str]]:
    """Create and return the active CYT log file handle."""
    paths = config.get("paths", {})
    log_dir = paths.get("log_dir", "logs")
    log_dir_path = pathlib.Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir_path / f'cyt_log_{time.strftime("%m%d%y_%H%M%S")}'
    log_file_name = str(log_file_path)
    return log_file_name, open(log_file_name, "w", buffering=1)


def discover_latest_kismet_db(db_path_glob: str) -> str:
    """Find newest Kismet database matching configured pattern."""
    list_of_files = glob.glob(db_path_glob)
    if not list_of_files:
        raise FileNotFoundError(f"No Kismet database files found at: {db_path_glob}")
    return max(list_of_files, key=os.path.getctime)


class MonitoringService:
    """Shared service for secure CYT monitoring operations."""

    def __init__(self, context: RuntimeContext, log_file: IO[str]):
        self.context = context
        self.log_file = log_file
        self.latest_db_file: Optional[str] = None
        self.monitor: Optional[SecureCYTMonitor] = None
        self.ignore_list: List[str] = []
        self.probe_ignore_list: List[str] = []

    @property
    def config(self) -> dict:
        return self.context.config

    def initialize(self) -> str:
        """Initialize ignore lists, DB selection, and tracking state."""
        self.ignore_list, self.probe_ignore_list = load_ignore_lists(self.config)

        logger.info(
            "Securely loaded %s MAC addresses and %s SSIDs",
            len(self.ignore_list),
            len(self.probe_ignore_list),
        )

        self.log_file.write(f"{len(self.ignore_list)} MACs added to ignore list.\n")
        self.log_file.write(
            f"{len(self.probe_ignore_list)} Probed SSIDs added to ignore list.\n"
        )

        self.latest_db_file = discover_latest_kismet_db(self.config["paths"]["kismet_logs"])
        self.log_file.write(f"Pulling data from: {self.latest_db_file}\n")

        self.monitor = SecureCYTMonitor(
            self.config,
            self.ignore_list,
            self.probe_ignore_list,
            self.log_file,
        )

        with SecureKismetDB(self.latest_db_file) as db:
            if not db.validate_connection():
                raise RuntimeError("Database validation failed")
            self.monitor.initialize_tracking_lists(db)

        return self.latest_db_file

    def run_cycle(self, cycle_number: int) -> None:
        """Execute one monitoring cycle and rotate lists when due."""
        if not self.latest_db_file or not self.monitor:
            raise RuntimeError("MonitoringService must be initialized before running")

        list_update_interval = self.config.get("timing", {}).get("list_update_interval", 5)
        with SecureKismetDB(self.latest_db_file) as db:
            self.monitor.process_current_activity(db)
            if cycle_number % list_update_interval == 0:
                logger.info("Rotating tracking lists (cycle %s)", cycle_number)
                self.monitor.rotate_tracking_lists(db)


class BackgroundMonitoringRunner:
    """Thread-safe monitor runner for GUI integration."""

    def __init__(self, config_path: str = "config.json", on_output: Optional[Callable[[str], None]] = None):
        self.config_path = config_path
        self.on_output = on_output
        self._stop_event = threading.Event()

    def _emit(self, message: str) -> None:
        if self.on_output:
            self.on_output(message)

    def run(self) -> int:
        """Run the monitor loop until stopped."""
        context = load_runtime_context(self.config_path)
        ensure_runtime_directories(context.config)
        _, cyt_log = create_cyt_log(context.config)
        service = MonitoringService(context, cyt_log)

        try:
            self._emit("Current Time: " + time.strftime("%Y-%m-%d %H:%M:%S"))
            latest_file = service.initialize()
            self._emit(f"{len(service.ignore_list)} MACs added to ignore list.")
            self._emit(f"{len(service.probe_ignore_list)} Probed SSIDs added to ignore list.")
            self._emit(f"Pulling data from: {latest_file}")
            self._emit("Initializing secure tracking lists...")
            self._emit("Initialization complete!")

            check_interval = context.config.get("timing", {}).get("check_interval", 60)
            list_update_interval = context.config.get("timing", {}).get("list_update_interval", 5)
            self._emit("SECURE MODE: All SQL injection vulnerabilities have been eliminated!")
            self._emit(
                f"Monitoring every {check_interval} seconds, updating lists every {list_update_interval} cycles"
            )

            cycle = 0
            while not self._stop_event.is_set():
                cycle += 1
                try:
                    service.run_cycle(cycle)
                except Exception as exc:
                    self._emit(f"Error in monitoring loop: {exc}")
                # Allows responsive shutdown without waiting full interval.
                if self._stop_event.wait(check_interval):
                    break

            self._emit("Shutting down gracefully...")
            return 0
        finally:
            cyt_log.close()

    def stop(self) -> None:
        """Request graceful stop."""
        self._stop_event.set()

    def terminate(self) -> None:
        """Subprocess-compatible shutdown alias for GUI cleanup paths."""
        self.stop()
