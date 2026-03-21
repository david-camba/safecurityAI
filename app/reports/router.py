from fastapi import APIRouter, Depends, HTTPException, Path as FastAPIPath
from .schemas import ReportsListResponse, ReportDetailResponse
from .services import ReportsService
from app.config import settings
from pathlib import Path

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def get_reports_service() -> ReportsService:
    return ReportsService(logs_dir=Path(settings.STORAGE_DIR))


@router.get("", response_model=ReportsListResponse)
def list_reports(service: ReportsService = Depends(get_reports_service)):
    return service.get_all_reports()


@router.get("/{filename}", response_model=ReportDetailResponse)
def get_report_detail(
    filename: str = FastAPIPath(..., pattern=r"^audit_report_\d{8}_\d{6}_.+\.md$"),
    service: ReportsService = Depends(get_reports_service),
):
    try:
        detail = service.get_report_by_filename(filename)
        if not detail:
            raise HTTPException(status_code=404, detail="Report not found.")
        return detail
    except IOError as e:
        raise HTTPException(status_code=500, detail=str(e))
