from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class User(Base):
    """User model for authentication and tracking."""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=True)
    role = Column(String(50), default="user")  # admin, user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    detections = relationship("Detection", back_populates="user", cascade="all, delete-orphan")


class Model(Base):
    """YOLOv8 model configuration and metadata."""
    __tablename__ = "models"

    model_id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), index=True, nullable=False)
    version = Column(String(50), nullable=False)
    file_path = Column(Text, nullable=False)
    num_classes = Column(Integer, nullable=False)
    class_names = Column(JSON, nullable=False)  # JSONB array of class names
    is_active = Column(Boolean, default=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    detections = relationship("Detection", back_populates="model")
    datasets = relationship("Dataset", back_populates="model")


class Detection(Base):
    """Individual detection run record."""
    __tablename__ = "detections"

    detection_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)
    model_id = Column(Integer, ForeignKey("models.model_id"), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    image_url = Column(Text, nullable=True)  # Cloudinary URL
    input_type = Column(String(50), nullable=False)  # 'image', 'video', 'webcam'
    confidence_thresh = Column(Float, default=0.5)
    total_objects = Column(Integer, default=0)
    processing_ms = Column(Integer, default=0)  # Processing time in milliseconds
    status = Column(String(30), default="completed")  # 'completed', 'failed', 'processing'
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="detections")
    model = relationship("Model", back_populates="detections")
    detected_objects = relationship("DetectedObject", back_populates="detection", cascade="all, delete-orphan")


class DetectedObject(Base):
    """Individual object detected within a detection run."""
    __tablename__ = "detected_objects"

    object_id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.detection_id"), index=True, nullable=False)
    label = Column(String(100), index=True, nullable=False)
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    class_id = Column(Integer, nullable=False)
    track_id = Column(Integer, nullable=True)  # For video tracking
    
    # Relationships
    detection = relationship("Detection", back_populates="detected_objects")


class Dataset(Base):
    """Training datasets linked to models."""
    __tablename__ = "datasets"

    dataset_id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.model_id"), index=True, nullable=False)
    dataset_name = Column(String(100), unique=True, index=True, nullable=False)
    source = Column(String(100), nullable=True)  # 'coco', 'roboflow', 'custom', etc.
    image_count = Column(Integer, default=0)
    annotation_format = Column(String(50), default="yolo")  # 'yolo', 'pascal_voc', 'coco'
    local_path = Column(Text, nullable=True)
    remote_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    model = relationship("Model", back_populates="datasets")
