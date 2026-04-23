#!/usr/bin/env python3
"""Raspberry Pi QC scanner kiosk application.

Scanner input is handled as keyboard events. Press Enter to submit a scanned
serial number.
"""

from __future__ import annotations

import argparse
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

import tkinter as tk

TS_PATTERNS = (
    re.compile(r"(?P<ts>\d{8}T\d{6}Z)"),
    re.compile(r"(?P<ts>\d{14})"),
)
STATUS_PATTERN = re.compile(r"(?:^|_)(?P<status>PASSED|FAILED)_", re.IGNORECASE)


class LookupStatus(str, Enum):
    NO_RESULT = "NO_RESULT"
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ResultFile:
    path: Path
    status: LookupStatus
    serial: str
    sort_key: tuple[float, str]


@dataclass(frozen=True)
class LookupResult:
    status: LookupStatus
    serial: str
    source_file: Optional[Path] = None



def normalize_serial(serial: str) -> str:
    return serial.strip().upper()



def extract_timestamp(stem: str, fallback_mtime: float) -> float:
    for pattern in TS_PATTERNS:
        match = pattern.search(stem)
        if not match:
            continue
        ts = match.group("ts")
        try:
            if "T" in ts:
                dt = datetime.strptime(ts, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            else:
                dt = datetime.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            continue
    return fallback_mtime



def parse_result_file(path: Path) -> Optional[ResultFile]:
    stem = path.stem
    match = STATUS_PATTERN.search(stem)
    if not match:
        return None

    status_text = match.group("status").upper()
    status = LookupStatus.PASS if status_text == "PASSED" else LookupStatus.FAIL

    serial_raw = stem[match.end() :]
    serial = normalize_serial(serial_raw)
    if not serial:
        return None

    mtime = path.stat().st_mtime
    sort_key = (extract_timestamp(stem, mtime), path.name)

    return ResultFile(path=path, status=status, serial=serial, sort_key=sort_key)



def lookup_latest_result(results_dir: Path, serial: str) -> LookupResult:
    serial_norm = normalize_serial(serial)
    latest: Optional[ResultFile] = None

    for entry in results_dir.iterdir():
        if not entry.is_file():
            continue
        # Quick early filter
        if serial_norm not in entry.stem.upper():
            continue

        parsed = parse_result_file(entry)
        if not parsed:
            continue
        if parsed.serial != serial_norm:
            continue

        if latest is None or parsed.sort_key > latest.sort_key:
            latest = parsed

    if latest is None:
        return LookupResult(status=LookupStatus.NO_RESULT, serial=serial_norm)
    return LookupResult(status=latest.status, serial=serial_norm, source_file=latest.path)


class KioskApp:
    def __init__(self, root: tk.Tk, results_dir: Path, pass_show_ms: int = 1000):
        self.root = root
        self.results_dir = results_dir
        self.pass_show_ms = pass_show_ms

        self.scan_buffer = ""
        self.state = "READY"
        self.pass_timer_id: Optional[str] = None

        self.root.title("QC Scanner Kiosk")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")

        self.label = tk.Label(
            self.root,
            text="Ready to scan",
            fg="white",
            bg="black",
            font=("Arial", 42, "bold"),
        )
        self.label.pack(expand=True, fill="both")

        self.root.bind("<Escape>", self._on_escape)
        self.root.bind("<Key>", self._on_key)
        self.root.bind("<Button-1>", self._on_tap)

    def _on_escape(self, _event: tk.Event) -> None:
        self.root.destroy()

    def _on_key(self, event: tk.Event) -> None:
        if self.state != "READY":
            return

        if event.keysym == "Return":
            serial = normalize_serial(self.scan_buffer)
            self.scan_buffer = ""
            if serial:
                self.handle_scan(serial)
            return

        if event.keysym == "BackSpace":
            self.scan_buffer = self.scan_buffer[:-1]
            return

        if event.char and event.char.isprintable():
            self.scan_buffer += event.char

    def _on_tap(self, _event: tk.Event) -> None:
        if self.state in {"SHOW_NO_RESULTS", "SHOW_FAIL"}:
            self.show_ready()

    def handle_scan(self, serial: str) -> None:
        result = lookup_latest_result(self.results_dir, serial)
        if result.status == LookupStatus.NO_RESULT:
            self.show_error("No Results Found")
            self.state = "SHOW_NO_RESULTS"
            return
        if result.status == LookupStatus.FAIL:
            self.show_error("Latest Result Found - Failure")
            self.state = "SHOW_FAIL"
            return

        self.show_pass()

    def show_ready(self) -> None:
        self._cancel_pass_timer()
        self.state = "READY"
        self.root.configure(bg="black")
        self.label.configure(bg="black", fg="white", text="Ready to scan")

    def show_error(self, message: str) -> None:
        self._cancel_pass_timer()
        self.root.configure(bg="#aa0000")
        self.label.configure(bg="#aa0000", fg="white", text=message)

    def show_pass(self) -> None:
        self._cancel_pass_timer()
        self.state = "SHOW_PASS"
        self.root.configure(bg="#008a00")
        self.label.configure(bg="#008a00", fg="white", text="PASS")
        self.pass_timer_id = self.root.after(self.pass_show_ms, self.show_ready)

    def _cancel_pass_timer(self) -> None:
        if self.pass_timer_id is not None:
            self.root.after_cancel(self.pass_timer_id)
            self.pass_timer_id = None



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run QC scanner kiosk app")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("./sample_data"),
        help="Directory containing QC result files",
    )
    parser.add_argument(
        "--pass-duration-ms",
        type=int,
        default=1000,
        help="How long to show green pass state in milliseconds",
    )
    return parser.parse_args()



def main() -> int:
    args = parse_args()
    results_dir = args.results_dir
    if not results_dir.exists() or not results_dir.is_dir():
        raise SystemExit(f"Results directory not found: {results_dir}")

    root = tk.Tk()
    app = KioskApp(root, results_dir=results_dir, pass_show_ms=args.pass_duration_ms)
    app.show_ready()
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
