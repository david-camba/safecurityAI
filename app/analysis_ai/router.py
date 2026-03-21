import logging
from starlette.websockets import WebSocketState
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.analysis_ai.services.ai_workflow import AIWorkflow
from app.analysis_ai.services.notifier import WebSocketNotifier
from app.reports.services import ReportsService
from app.config import settings
from pathlib import Path

logger = logging.getLogger("analysis_ai_router")
router = APIRouter(prefix="/ws", tags=["Analysis AI"])


def get_ai_workflow() -> AIWorkflow:
    return AIWorkflow()


def get_reports_service() -> ReportsService:
    return ReportsService(logs_dir=Path(settings.STORAGE_DIR))


@router.websocket("/analyze")
async def analyze_endpoint(
    websocket: WebSocket,
    ai_workflow: AIWorkflow = Depends(get_ai_workflow),
    reports_service: ReportsService = Depends(get_reports_service),
):
    await websocket.accept()
    notifier = WebSocketNotifier(websocket)

    try:
        raw_audit_data = await ai_workflow.run_analysis(notifier)

        # Save the audit log to disk and send the final report to the client
        audit_data = reports_service.save_audit_log(raw_audit_data)
        await notifier.send_completion(audit_data.final_report)

    except WebSocketDisconnect:
        logger.warning("Client disconnected.")
    except Exception as e:
        if isinstance(e, RuntimeError) and "Unexpected ASGI message" in str(e):
            logger.warning("Client connection lost mid-execution.")
        else:
            logger.error(f"Execution failure: {str(e)}", exc_info=True)
            if websocket.client_state == WebSocketState.CONNECTED:
                await notifier.send_error(f"Analysis aborted: {str(e)}")
    finally:
        if websocket.application_state == WebSocketState.CONNECTED:
            try:
                await websocket.close()
            except Exception:
                pass
