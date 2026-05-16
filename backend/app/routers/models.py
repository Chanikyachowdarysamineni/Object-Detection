from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.core.database import get_db
from app.core.logging import logger
from app.schemas.schemas import ModelResponse, ModelCreate
from app.models.models import Model, Detection

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/", response_model=List[ModelResponse])
async def list_models(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """
    Get list of available models.
    
    Args:
        active_only: If True, only return active models
    """
    try:
        query = db.query(Model)
        if active_only:
            query = query.filter(Model.is_active == True)
        
        models = query.all()
        return models
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific model."""
    try:
        model = db.query(Model).filter(Model.model_id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=ModelResponse)
async def create_model(
    model_data: ModelCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new model record.
    
    Args:
        model_data: Model information
    """
    try:
        db_model = Model(
            model_name=model_data.model_name,
            version=model_data.version,
            file_path=model_data.file_path,
            num_classes=model_data.num_classes,
            class_names=model_data.class_names,
            is_active=True,
        )
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        
        logger.info(f"Model created: {model_data.model_name} v{model_data.version}")
        return db_model
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    model_data: ModelCreate,
    db: Session = Depends(get_db),
):
    """Update an existing model."""
    try:
        db_model = db.query(Model).filter(Model.model_id == model_id).first()
        if not db_model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        db_model.model_name = model_data.model_name
        db_model.version = model_data.version
        db_model.file_path = model_data.file_path
        db_model.num_classes = model_data.num_classes
        db_model.class_names = model_data.class_names
        
        db.commit()
        db.refresh(db_model)
        
        logger.info(f"Model updated: {model_id}")
        return db_model
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_id}")
async def delete_model(model_id: int, db: Session = Depends(get_db)):
    """Delete a model (soft delete by marking inactive)."""
    try:
        db_model = db.query(Model).filter(Model.model_id == model_id).first()
        if not db_model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Soft delete
        db_model.is_active = False
        db.commit()
        
        logger.info(f"Model deactivated: {model_id}")
        return {"message": "Model deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/statistics")
async def get_model_statistics(model_id: int, db: Session = Depends(get_db)):
    """Get usage statistics for a specific model."""
    try:
        model = db.query(Model).filter(Model.model_id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Get statistics
        total_detections = db.query(func.count(Detection.detection_id)).filter(
            Detection.model_id == model_id
        ).scalar()
        
        total_objects = db.query(func.sum(Detection.total_objects)).filter(
            Detection.model_id == model_id
        ).scalar() or 0
        
        avg_processing_ms = db.query(func.avg(Detection.processing_ms)).filter(
            Detection.model_id == model_id
        ).scalar() or 0
        
        return {
            "model_id": model_id,
            "model_name": model.model_name,
            "total_detections": total_detections,
            "total_objects": total_objects,
            "average_processing_ms": round(avg_processing_ms, 2),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
