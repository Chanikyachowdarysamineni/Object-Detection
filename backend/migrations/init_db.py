"""
Database Migration Script - Initialize PostgreSQL Schema
Run this script to set up the database tables.
"""

import os
import sys
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.config import settings
from app.core.database import Base
from app.models.models import User, Model, Detection, DetectedObject, Dataset

# Load environment variables
load_dotenv()


def init_db():
    """Initialize database with all tables."""
    print("🔄 Initializing database...")
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    
    # Seed default model
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if YOLOv8n model already exists
        existing_model = session.query(Model).filter(
            Model.model_name == "YOLOv8n"
        ).first()
        
        if not existing_model:
            # Create default YOLOv8n model
            coco_classes = [
                "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
                "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
                "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
                "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis",
                "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
                "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork", "knife",
                "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
                "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed",
                "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "microwave",
                "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
                "teddy bear", "hair drier", "toothbrush"
            ]
            
            default_model = Model(
                model_name="YOLOv8n",
                version="8.0.0",
                file_path="yolov8n.pt",
                num_classes=80,
                class_names=coco_classes,
                is_active=True,
            )
            session.add(default_model)
            session.commit()
            print("✅ Default YOLOv8n model created")
        
        # Create default user if needed
        existing_user = session.query(User).filter(
            User.username == "admin"
        ).first()
        
        if not existing_user:
            from app.core.security import get_password_hash
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_active=True,
            )
            session.add(admin_user)
            session.commit()
            print("✅ Default admin user created (username: admin, password: admin123)")
        
        print("✅ Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding data: {str(e)}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        sys.exit(1)
