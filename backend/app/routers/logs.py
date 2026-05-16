from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List

from ..core.database import get_db
from ..core.logging import logger
from ..schemas.schemas import (
    DetectionLogResponse,
    DetectionStats,
    DetectionLogFilter,
)
from ..models.models import Detection, DetectedObject

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/detections", response_model=List[DetectionLogResponse])
async def get_detections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    input_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    class_label: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get paginated detection logs with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Number of records to return
        input_type: Filter by input type ('image', 'video', 'webcam')
        start_date: Filter by start date
        end_date: Filter by end date
        class_label: Filter by detected class label
    """
    try:
        query = db.query(Detection)
        
        # Apply filters
        if input_type:
            query = query.filter(Detection.input_type == input_type)
        
        if start_date:
            query = query.filter(Detection.created_at >= start_date)
        
        if end_date:
            query = query.filter(Detection.created_at <= end_date)
        
        if class_label:
            # Join with detected_objects and filter
            query = query.join(DetectedObject).filter(
                DetectedObject.label == class_label
            ).distinct()
        
        # Order by most recent first
        query = query.order_by(desc(Detection.created_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        detections = query.offset(skip).limit(limit).all()
        
        return detections
        
    except Exception as e:
        logger.error(f"Error fetching detections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detection/{detection_id}", response_model=dict)
async def get_detection_detail(detection_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific detection."""
    try:
        detection = db.query(Detection).filter(
            Detection.detection_id == detection_id
        ).first()
        
        if not detection:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        # Get detected objects
        objects = db.query(DetectedObject).filter(
            DetectedObject.detection_id == detection_id
        ).all()
        
        return {
            "detection": detection,
            "objects": objects,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching detection detail: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=DetectionStats)
async def get_statistics(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get detection statistics for the specified period.
    
    Args:
        days: Number of days to include in statistics
    """
    try:
        # Calculate date threshold
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get detections
        detections = db.query(Detection).filter(
            Detection.created_at >= start_date
        ).all()
        
        if not detections:
            return DetectionStats(
                total_detections=0,
                total_objects=0,
                average_confidence=0.0,
                most_common_class="N/A",
                processing_time_avg_ms=0.0,
            )
        
        # Calculate statistics
        total_detections = len(detections)
        total_objects = sum(d.total_objects for d in detections)
        avg_processing_ms = sum(d.processing_ms for d in detections) / total_detections if total_detections > 0 else 0
        
        # Get all detected objects
        objects = db.query(DetectedObject).join(Detection).filter(
            Detection.created_at >= start_date
        ).all()
        
        # Calculate average confidence and most common class
        avg_confidence = 0.0
        most_common_class = "N/A"
        
        if objects:
            avg_confidence = sum(obj.confidence for obj in objects) / len(objects)
            
            # Find most common class
            class_counts = {}
            for obj in objects:
                class_counts[obj.label] = class_counts.get(obj.label, 0) + 1
            
            if class_counts:
                most_common_class = max(class_counts, key=class_counts.get)
        
        return DetectionStats(
            total_detections=total_detections,
            total_objects=total_objects,
            average_confidence=round(avg_confidence, 3),
            most_common_class=most_common_class,
            processing_time_avg_ms=round(avg_processing_ms, 2),
        )
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class-distribution")
async def get_class_distribution(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get distribution of detected classes over the specified period.
    
    Args:
        days: Number of days to include
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        objects = db.query(DetectedObject).join(Detection).filter(
            Detection.created_at >= start_date
        ).all()
        
        # Build distribution
        class_distribution = {}
        for obj in objects:
            class_distribution[obj.label] = class_distribution.get(obj.label, 0) + 1
        
        # Sort by count
        sorted_distribution = sorted(
            class_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "distribution": dict(sorted_distribution),
            "total_objects": len(objects),
        }
        
    except Exception as e:
        logger.error(f"Error getting class distribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-csv")
async def export_as_csv(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Export detection logs as CSV.
    
    Args:
        days: Number of days to include
    """
    try:
        import csv
        import io
        from fastapi.responses import StreamingResponse
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        detections = db.query(Detection).filter(
            Detection.created_at >= start_date
        ).order_by(desc(Detection.created_at)).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Detection ID",
            "Filename",
            "Input Type",
            "Total Objects",
            "Processing Time (ms)",
            "Status",
            "Created At",
        ])
        
        # Write data
        for detection in detections:
            writer.writerow([
                detection.detection_id,
                detection.filename,
                detection.input_type,
                detection.total_objects,
                detection.processing_ms,
                detection.status,
                detection.created_at.isoformat(),
            ])
        
        # Create response
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=detections.csv"},
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
