from fastapi import APIRouter, Depends, HTTPException
from .schemas import FeatureSuggestionsResponse
from .services import SuggestionsService
from app.config import settings
from pathlib import Path

router = APIRouter(prefix="/api/features", tags=["Agent Suggestions"])


def get_service() -> SuggestionsService:
    return SuggestionsService(Path(settings.SUGGESTIONS_FILE))


@router.get("", response_model=FeatureSuggestionsResponse)
def list_suggestions(service: SuggestionsService = Depends(get_service)):
    try:
        return service.get_all_suggestions()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Log file missing.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
