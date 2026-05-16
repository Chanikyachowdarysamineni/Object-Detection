from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# User Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Token Schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# Detected Object Schemas
class DetectedObjectResponse(BaseModel):
    object_id: int
    label: str
    confidence: float = Field(..., ge=0, le=1)
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    class_id: int
    track_id: Optional[int] = None

    class Config:
        from_attributes = True


class DetectedObjectCreate(BaseModel):
    label: str
    confidence: float = Field(..., ge=0, le=1)
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    class_id: int
    track_id: Optional[int] = None


# Detection Schemas
class DetectionResponse(BaseModel):
    detection_id: int
    user_id: Optional[int]
    model_id: int
    filename: str
    image_url: Optional[str]
    input_type: str
    confidence_thresh: float
    total_objects: int
    processing_ms: int
    status: str
    error_message: Optional[str]
    created_at: datetime
    detected_objects: List[DetectedObjectResponse] = []

    class Config:
        from_attributes = True


class DetectionCreate(BaseModel):
    model_id: int
    filename: str
    input_type: str
    confidence_thresh: float = 0.5


# Detection Request Schemas
class ImageDetectionRequest(BaseModel):
    confidence_threshold: float = Field(0.5, ge=0, le=1)
    iou_threshold: float = Field(0.45, ge=0, le=1)


class VideoDetectionRequest(BaseModel):
    confidence_threshold: float = Field(0.5, ge=0, le=1)
    iou_threshold: float = Field(0.45, ge=0, le=1)
    frame_skip: int = Field(1, ge=1)  # Process every nth frame


class WebcamDetectionRequest(BaseModel):
    confidence_threshold: float = Field(0.5, ge=0, le=1)
    iou_threshold: float = Field(0.45, ge=0, le=1)
    stream_duration: int = Field(30, ge=1)  # Duration in seconds


# Model Schemas
class ModelResponse(BaseModel):
    model_id: int
    model_name: str
    version: str
    file_path: str
    num_classes: int
    class_names: List[str]
    is_active: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ModelCreate(BaseModel):
    model_name: str
    version: str
    file_path: str
    num_classes: int
    class_names: List[str]


# Dataset Schemas
class DatasetResponse(BaseModel):
    dataset_id: int
    model_id: int
    dataset_name: str
    source: Optional[str]
    image_count: int
    annotation_format: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetCreate(BaseModel):
    model_id: int
    dataset_name: str
    source: Optional[str] = None
    image_count: int = 0
    annotation_format: str = "yolo"
    local_path: Optional[str] = None
    remote_url: Optional[str] = None


# Detection Statistics
class DetectionStats(BaseModel):
    total_detections: int
    total_objects: int
    average_confidence: float
    most_common_class: str
    processing_time_avg_ms: float


class DetectionLogResponse(BaseModel):
    detection_id: int
    filename: str
    input_type: str
    total_objects: int
    processing_ms: int
    created_at: datetime
    status: str


class DetectionLogFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    input_type: Optional[str] = None  # 'image', 'video', 'webcam'
    class_label: Optional[str] = None
    min_confidence: float = Field(0.0, ge=0, le=1)
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=1000)


class TrainingConfigRequest(BaseModel):
    dataset_id: int
    epochs: int = Field(50, ge=1, le=500)
    batch_size: int = Field(16, ge=1, le=128)
    image_size: int = Field(640, ge=320, le=1280)
    device: str = "0"  # "0" for GPU, "cpu" for CPU
    learning_rate: float = Field(0.001, ge=0.00001, le=0.1)
