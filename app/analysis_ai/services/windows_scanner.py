import asyncio
import os
import glob
import logging
import subprocess
import threading
from datetime import datetime
from app.config import settings
from pathlib import Path

from app.analysis_ai.services.notifier import BaseNotifier

logger = logging.getLogger(__name__)


async def run_local_scan(
    ps_script_path: str = "scan_windows.ps1", notifier: BaseNotifier = None
) -> str:
    """
    Executes the system telemetry collection payload.
    Utilizes a hybrid threading/async architecture to stream standard output
    in real-time to the active notifier without blocking the main event loop.
    """
    logger.info("Initializing local Windows telemetry collector...")

    scans_dir = Path(settings.SCANS_DIR)

    # ---------------------------------------------------------
    # DEBUG ENVIRONMENT HANDLING
    # ---------------------------------------------------------
    if settings.DEBUG_ON:
        logger.warning("DEBUG_ON enabled. Bypassing live telemetry collection.")
        if os.path.exists(scans_dir):
            search_pattern = os.path.join(scans_dir, "*", "complete_scan.txt")
            scan_files = glob.glob(search_pattern)

            if scan_files:
                latest_scan = max(scan_files, key=os.path.getctime)
                logger.info(f"Loading historical telemetry: {latest_scan}")

                def _read_debug_file() -> str:
                    with open(latest_scan, "r", encoding="utf-8") as f:
                        return f.read()

                return await asyncio.to_thread(_read_debug_file)

        logger.warning("No historical scans found. Falling back to live execution.")

    # ---------------------------------------------------------
    # LIVE TELEMETRY EXECUTION
    # ---------------------------------------------------------
    if not os.path.exists(ps_script_path):
        raise FileNotFoundError(
            f"Missing required telemetry payload at: {ps_script_path}"
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_scan_dir = os.path.join(scans_dir, timestamp)
    os.makedirs(current_scan_dir, exist_ok=True)

    result_file = os.path.join(current_scan_dir, "complete_scan.txt")

    command = [
        "powershell.exe",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        ps_script_path,
        "-OutputDir",
        current_scan_dir,
    ]

    # Cross-thread communication primitives
    loop = asyncio.get_running_loop()
    stream_queue = asyncio.Queue()

    def _run_subprocess():
        """Background worker handling synchronous I/O streams."""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore",
                bufsize=1,
            )

            for line in process.stdout:
                clean_line = line.strip()
                if clean_line:
                    loop.call_soon_threadsafe(
                        stream_queue.put_nowait, ("LOG", clean_line)
                    )

            process.wait()

            if process.returncode != 0:
                loop.call_soon_threadsafe(
                    stream_queue.put_nowait,
                    ("ERROR", f"Process exited with code {process.returncode}"),
                )
            else:
                loop.call_soon_threadsafe(stream_queue.put_nowait, ("DONE", None))

        except Exception as e:
            loop.call_soon_threadsafe(stream_queue.put_nowait, ("ERROR", str(e)))
        finally:
            if process and process.poll() is None:
                logger.warning("Forcing the closure of the PowerShell process...")
                process.kill()

    # Dispatch blocking process to a background thread
    worker_thread = threading.Thread(target=_run_subprocess, daemon=True)
    worker_thread.start()

    # Consume the I/O stream asynchronously
    while True:
        msg_type, payload = await stream_queue.get()

        if msg_type == "DONE":
            break
        elif msg_type == "ERROR":
            logger.error(f"Telemetry execution failed: {payload}")
            raise RuntimeError(f"Scanner process terminated unexpectedly: {payload}")
        elif msg_type == "LOG":
            if notifier:
                await notifier.send_log(f"[WINDOWS SCANNER] {payload}")

    await asyncio.to_thread(worker_thread.join)

    if not os.path.exists(result_file):
        raise FileNotFoundError(
            f"Expected telemetry payload not generated: {result_file}"
        )

    def _read_output_file() -> str:
        """Isolated synchronous file read."""
        with open(result_file, "r", encoding="utf-8") as f:
            return f.read()

    system_data = await asyncio.to_thread(_read_output_file)
    logger.info(
        f"Telemetry collection complete. Memory allocation: {len(system_data)} bytes."
    )

    return system_data
