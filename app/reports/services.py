import re
import logging
from datetime import datetime
from pathlib import Path
from pydantic import ValidationError

from .schemas import (
    AuditReportCreate,
    ReportItem,
    ReportsListResponse,
    ReportDetailResponse,
)

logger = logging.getLogger(__name__)

# Root-level logs directory mapping
LOG_PATTERN = re.compile(r"^audit_report_(\d{8})_(\d{6})_(.+)\.md$")
END_OF_REPORT_TAG = "<!-- END-OF-REPORT -->"


class ReportsService:
    """
    Encapsulates all domain logic for forensic reports:
    validation, persistence, and retrieval.
    """

    def __init__(self, logs_dir: Path | None = None):
        self.logs_dir = logs_dir

    def save_audit_log(self, raw_data: dict) -> str:
        """
        Validates raw execution state against the domain contract and persists it.
        """
        try:
            # 1. Anti-Corruption Layer: Validate incoming raw dict
            data = AuditReportCreate(**raw_data)
        except ValidationError as e:
            logger.error(f"Failed to validate audit data payload: {e}")
            raise ValueError("Invalid audit data format provided to Reports domain.")

        self.logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        status_suffix = "safe" if data.is_system_safe else "infected"
        log_filename = self.logs_dir / f"audit_report_{timestamp}_{status_suffix}.md"

        try:
            with open(log_filename, "w", encoding="utf-8") as f:
                # Final Report
                f.write(data.final_report)
                f.write(f"\n{END_OF_REPORT_TAG}\n")
                f.write("\n---\n")

                # Execution Metadata
                f.write("## ⚙️ EXECUTION METADATA (LangGraph)\n")
                f.write(f"- **Total Iterations:** {data.iteration_count}\n")
                f.write(f"- **Agent Finished:** {data.is_finished}\n")
                f.write(f"- **Pending Tools:** {len(data.tool_requests)}\n")
                f.write("\n---\n\n")

                # Reasoning History
                f.write("## 🧠 REASONING AND ACTIONS HISTORY\n\n")
                if not data.history:
                    f.write("No reasoning history recorded.\n")
                else:
                    for msg in data.history:
                        role = msg.get("role", "UNKNOWN").upper()
                        content = msg.get("content", "")
                        f.write(f"### [{role}]\n{content}\n\n")
                f.write("\n---\n\n")

                # Raw System Data (Collapsible)
                f.write("## 💾 RAW SYSTEM TELEMETRY\n")
                f.write(
                    "<details>\n<summary>Click to expand PowerShell telemetry</summary>\n\n```json\n"
                )
                f.write(data.system_data)
                f.write("\n```\n</details>\n")

            logger.info(f"Audit log successfully saved at: {log_filename.name}")
            return data

        except Exception as e:
            logger.error(
                f"Failed to persist audit log to disk: {str(e)}", exc_info=True
            )
            raise IOError("Storage failure during report generation.")

    def get_all_reports(self) -> ReportsListResponse:
        """Scans the storage directory and constructs a sorted listing of all reports."""
        if not self.logs_dir.exists() or not self.logs_dir.is_dir():
            return ReportsListResponse(reports=[], total_count=0)

        parsed_reports = []

        for file_path in self.logs_dir.glob("audit_report_*.md"):
            match = LOG_PATTERN.match(file_path.name)

            if match:
                raw_date, raw_time, status = match.groups()
                parsed_reports.append(
                    ReportItem(
                        filename=file_path.name,
                        date=f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}",
                        time=f"{raw_time[:2]}:{raw_time[2:4]}:{raw_time[4:]}",
                        status=status.lower(),
                    )
                )

        parsed_reports.sort(key=lambda x: (x.date, x.time), reverse=True)

        return ReportsListResponse(
            reports=parsed_reports, total_count=len(parsed_reports)
        )

    def get_report_by_filename(self, filename: str) -> ReportDetailResponse | None:
        """Extracts content from a specific report up to the established delimiter."""
        file_path = self.logs_dir / filename

        if not file_path.exists() or not file_path.is_file():
            return None

        match = LOG_PATTERN.match(filename)
        if not match:
            return None

        raw_date, raw_time, _ = match.groups()
        formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
        formatted_time = f"{raw_time[:2]}:{raw_time[2:4]}:{raw_time[4:]}"

        content_lines = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if END_OF_REPORT_TAG in line:
                        break
                    content_lines.append(line)
        except Exception as e:
            logger.error(f"I/O error reading report {filename}: {e}")
            raise IOError("Failed to read report data.")

        return ReportDetailResponse(
            content="".join(content_lines),
            date=formatted_date,
            time=formatted_time,
        )
