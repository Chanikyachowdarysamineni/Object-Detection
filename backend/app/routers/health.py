from fastapi import APIRouter, HTTPException
from app.core.logging import logger
from app.services.yolo_service import YOLOv8Service

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
async def health_check():
    """Check if API is running."""
    return {"status": "ok", "message": "API is running"}


@router.get("/model-status")
async def model_status():
    """Check if YOLOv8 model is loaded and ready."""
    try:
        yolo_service = YOLOv8Service()
        model_info = yolo_service.get_model_info()
        
        if not model_info:
            return {"status": "error", "message": "Model not loaded"}
        
        return {
            "status": "ready",
            "model_info": model_info,
        }
    except Exception as e:
        logger.error(f"Model status check failed: {str(e)}")
        return {"status": "error", "message": str(e)}
