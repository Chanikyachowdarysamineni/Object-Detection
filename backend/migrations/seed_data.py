"""
Database Seeding Script
Initialize database with default model and test data
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.models import Model, User
from app.core.logging import logger


def init_database():
    """Initialize database with tables and seed data."""
    try:
        # Create all tables
        logger.info("[DB] Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("[OK] Database tables created")
        
        # Create session
        db: Session = SessionLocal()
        
        try:
            # Check if default model exists
            existing_model = db.query(Model).filter(
                Model.model_name == "yolov8n"
            ).first()
            
            if not existing_model:
                logger.info("[DB] Creating default YOLOv8 model...")
                
                # Create default model
                default_model = Model(
                    model_name="yolov8n",
                    version="1.0",
                    file_path="yolov8n.pt",
                    num_classes=80,
                    class_names=[
                        "person", "bicycle", "car", "motorcycle", "airplane",
                        "bus", "train", "truck", "boat", "traffic light",
                        "fire hydrant", "stop sign", "parking meter", "bench",
                        "bird", "cat", "dog", "horse", "sheep", "cow",
                        "elephant", "bear", "zebra", "giraffe", "backpack",
                        "umbrella", "handbag", "tie", "suitcase", "frisbee",
                        "skis", "snowboard", "sports ball", "kite",
                        "baseball bat", "baseball glove", "skateboard",
                        "surfboard", "tennis racket", "bottle", "wine glass",
                        "cup", "fork", "knife", "spoon", "bowl", "banana",
                        "apple", "sandwich", "orange", "broccoli", "carrot",
                        "hot dog", "pizza", "donut", "cake", "chair", "couch",
                        "potted plant", "bed", "dining table", "toilet", "tv",
                        "laptop", "mouse", "remote", "keyboard", "cell phone",
                        "microwave", "oven", "toaster", "sink", "refrigerator",
                        "book", "clock", "vase", "scissors", "teddy bear",
                        "hair drier", "toothbrush"
                    ],
                    is_active=True,
                )
                db.add(default_model)
                db.commit()
                logger.info("[OK] Default model created")
            else:
                logger.info("[OK] Default model already exists")
            
            # Check if default user exists
            existing_user = db.query(User).filter(
                User.username == "admin"
            ).first()
            
            if not existing_user:
                logger.info("[DB] Creating default admin user...")
                
                admin_user = User(
                    username="admin",
                    email="admin@detection.local",
                    password_hash=None,  # Password not hashed in this simple setup
                    role="admin",
                    is_active=True,
                )
                db.add(admin_user)
                db.commit()
                logger.info("[OK] Default admin user created")
            else:
                logger.info("[OK] Default admin user already exists")
            
            logger.info("[OK] Database initialization complete")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ERROR] Database initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    init_database()
