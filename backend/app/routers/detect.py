from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import io
from PIL import Image
import cv2
import numpy as np

from ..core.database import get_db
from ..core.logging import logger
from ..schemas.schemas import (
    DetectionResponse,
    ImageDetectionRequest,
    VideoDetectionRequest,
)
from ..models.models import Detection, DetectedObject, Model
from ..services.yolo_service import YOLOv8Service
from ..core.config import settings

router = APIRouter(prefix="/api/detect", tags=["detection"])
yolo_service = YOLOv8Service()


@router.post("/image", response_model=DetectionResponse)
async def detect_image(
    file: UploadFile = File(...),
    confidence_threshold: float = 0.5,
    iou_threshold: float = 0.45,
    model_id: int = 1,
    user_id: int = None,
    db: Session = Depends(get_db),
):
    """
    Detect objects in uploaded image.
    
    Args:
        file: Image file to process (JPG, PNG, etc.)
        confidence_threshold: Detection confidence threshold (0.0-1.0)
        iou_threshold: IOU threshold for NMS (0.0-1.0)
        model_id: ID of model to use
        user_id: Optional user ID for logging
        
    Returns:
        Detection results with detected objects
    """
    try:
        # Validate input file
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        # Check file extension
        if not file.filename:
            raise HTTPException(status_code=400, detail="File has no name")
        
        allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
        file_ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Validate thresholds
        confidence_threshold = max(0.0, min(1.0, confidence_threshold))
        iou_threshold = max(0.0, min(1.0, iou_threshold))
        
        # Read and decode image
        image_array = np.frombuffer(file_content, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid or corrupted image file")
        
        # Check image dimensions
        height, width = image.shape[:2]
        if width < 32 or height < 32:
            raise HTTPException(status_code=400, detail="Image too small (min 32x32)")
        if width > 10000 or height > 10000:
            raise HTTPException(status_code=400, detail="Image too large (max 10000x10000)")
        
        # Run detection
        detections, processing_ms = yolo_service.detect_objects(
            image,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
            image_size=settings.IMAGE_SIZE,
        )
        
        # Get model
        model = db.query(Model).filter(Model.model_id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Save detection to database
        db_detection = Detection(
            user_id=user_id,
            model_id=model_id,
            filename=file.filename,
            input_type="image",
            confidence_thresh=confidence_threshold,
            total_objects=len(detections),
            processing_ms=processing_ms,
            status="completed",
        )
        db.add(db_detection)
        db.flush()
        
        # Save detected objects
        for det in detections:
            try:
                db_object = DetectedObject(
                    detection_id=db_detection.detection_id,
                    label=det.get("label", "Unknown"),
                    confidence=float(det.get("confidence", 0.0)),
                    bbox_x1=float(det["bbox"]["x1"]),
                    bbox_y1=float(det["bbox"]["y1"]),
                    bbox_x2=float(det["bbox"]["x2"]),
                    bbox_y2=float(det["bbox"]["y2"]),
                    class_id=int(det.get("class_id", 0)),
                )
                db.add(db_object)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error saving detected object: {str(e)}")
                continue
        
        db.commit()
        db.refresh(db_detection)
        
        logger.info(f"[OK] Image detection: {file.filename}, {len(detections)} objects in {processing_ms}ms")
        return db_detection
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[ERROR] Image detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/video", response_model=dict)
async def detect_video(
    file: UploadFile = File(...),
    confidence_threshold: float = 0.5,
    iou_threshold: float = 0.45,
    frame_skip: int = 1,
    model_id: int = 1,
    user_id: int = None,
    db: Session = Depends(get_db),
):
    """
    Detect objects in uploaded video file.
    
    Args:
        file: Video file to process (MP4, AVI, etc.)
        confidence_threshold: Detection confidence threshold (0.0-1.0)
        iou_threshold: IOU threshold for NMS (0.0-1.0)
        frame_skip: Process every nth frame (1=process all, 2=every 2nd, etc.)
        model_id: ID of model to use
        user_id: Optional user ID for logging
        
    Returns:
        Detection results with output video path
    """
    import tempfile
    import os
    
    tmp_file_path = None
    
    try:
        # Validate input file
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        # Check file extension
        if not file.filename:
            raise HTTPException(status_code=400, detail="File has no name")
        
        allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
        file_ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Validate parameters
        confidence_threshold = max(0.0, min(1.0, confidence_threshold))
        iou_threshold = max(0.0, min(1.0, iou_threshold))
        frame_skip = max(1, min(30, frame_skip))  # Limit frame skip to 1-30
        
        # Save video temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name
        
        # Run video detection
        output_path, all_detections, total_time = yolo_service.detect_from_video_file(
            tmp_file_path,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
            frame_skip=frame_skip,
        )
        
        # Get model
        model = db.query(Model).filter(Model.model_id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Save detection to database
        db_detection = Detection(
            user_id=user_id,
            model_id=model_id,
            filename=file.filename,
            input_type="video",
            confidence_thresh=confidence_threshold,
            total_objects=len(all_detections),
            processing_ms=total_time,
            status="completed",
        )
        db.add(db_detection)
        db.flush()
        
        # Save detected objects (limit to avoid DB bloat)
        for i, det in enumerate(all_detections[:settings.MAX_DETECTIONS]):
            try:
                db_object = DetectedObject(
                    detection_id=db_detection.detection_id,
                    label=det.get("label", "Unknown"),
                    confidence=float(det.get("confidence", 0.0)),
                    bbox_x1=float(det["bbox"]["x1"]),
                    bbox_y1=float(det["bbox"]["y1"]),
                    bbox_x2=float(det["bbox"]["x2"]),
                    bbox_y2=float(det["bbox"]["y2"]),
                    class_id=int(det.get("class_id", 0)),
                )
                db.add(db_object)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error saving video detection {i}: {str(e)}")
                continue
        
        db.commit()
        
        logger.info(f"[OK] Video detection: {file.filename}, {len(all_detections)} objects in {total_time}ms")
        
        return {
            "detection_id": db_detection.detection_id,
            "total_objects": len(all_detections),
            "processing_ms": total_time,
            "output_video": output_path,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if db:
            db.rollback()
        logger.error(f"[ERROR] Video detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Video detection failed: {str(e)}")
    finally:
        # Clean up temporary file
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
            except Exception as e:
                logger.warning(f"Could not delete temp file {tmp_file_path}: {str(e)}")


@router.get("/models")
async def get_available_models(db: Session = Depends(get_db)):
    """Get list of available models."""
    try:
        models = db.query(Model).filter(Model.is_active == True).all()
        return models
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-info")
async def get_model_info():
    """Get current YOLOv8 model information."""
    try:
        info = yolo_service.get_model_info()
        return info
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
