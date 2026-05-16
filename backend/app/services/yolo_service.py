import cv2
import numpy as np
from typing import List, Tuple, Optional
import torch
from ultralytics import YOLO
from ..core.config import settings
from ..core.logging import logger
from pathlib import Path
import time


class YOLOv8Service:
    """Service for YOLOv8 model inference."""

    _instance = None
    _model = None
    _device = None

    def __new__(cls):
        """Singleton pattern to ensure only one model instance."""
        if cls._instance is None:
            cls._instance = super(YOLOv8Service, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize YOLOv8 service and load model."""
        if self._model is None:
            self.load_model()

    def _get_device(self) -> str:
        """Get the best available device."""
        if self._device is not None:
            return self._device
        
        try:
            if settings.DEVICE == "cpu":
                self._device = "cpu"
            else:
                # Try to use GPU
                device_id = int(settings.DEVICE)
                if torch.cuda.is_available():
                    if device_id < torch.cuda.device_count():
                        self._device = device_id
                    else:
                        logger.warning(f"GPU {device_id} not available, using GPU 0")
                        self._device = 0
                else:
                    logger.warning("CUDA not available, falling back to CPU")
                    self._device = "cpu"
        except (ValueError, AttributeError):
            logger.warning(f"Invalid DEVICE setting: {settings.DEVICE}, using CPU")
            self._device = "cpu"
        
        logger.info(f"Using device: {self._device}")
        return self._device

    def load_model(self) -> None:
        """Load YOLOv8 model from file."""
        try:
            logger.info("Loading YOLOv8 model from " + settings.MODEL_PATH)
            
            # Get device
            device = self._get_device()
            
            # PyTorch 2.6+ compatibility: Patch torch.load to disable weights_only
            # This is needed because ultralytics internally calls torch.load without weights_only=False
            original_load = torch.load
            def patched_torch_load(*args, **kwargs):
                # Set weights_only=False if not explicitly set
                if 'weights_only' not in kwargs:
                    kwargs['weights_only'] = False
                return original_load(*args, **kwargs)
            
            torch.load = patched_torch_load
            
            try:
                # Load model with automatic downloading if needed
                self._model = YOLO(settings.MODEL_PATH, task="detect")
            finally:
                # Restore original torch.load
                torch.load = original_load
            
            # Move to device
            try:
                self._model.to(device)
            except Exception as e:
                logger.warning("Could not move model to device " + str(device) + ": " + str(e))
            
            # Verify model is loaded
            if self._model is None or self._model.model is None:
                raise ValueError("Model failed to load properly")
            
            logger.info("YOLOv8 model loaded successfully on device: " + str(device))
            
        except Exception as e:
            logger.error("Failed to load YOLOv8 model: " + str(e))
            raise

    def detect_objects(
        self,
        source,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        image_size: int = 640,
    ) -> Tuple[List[dict], int]:
        """
        Detect objects in image or frame.
        
        Args:
            source: Image array (numpy) or file path
            confidence_threshold: Minimum confidence score
            iou_threshold: IOU threshold for NMS
            image_size: Input image size
            
        Returns:
            Tuple of (detections list, processing time in ms)
        """
        if self._model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            start_time = time.time()
            
            # Validate inputs
            confidence_threshold = max(0.0, min(1.0, confidence_threshold))
            iou_threshold = max(0.0, min(1.0, iou_threshold))
            
            # Run inference
            results = self._model(
                source,
                conf=confidence_threshold,
                iou=iou_threshold,
                imgsz=image_size,
                verbose=False,
            )
            
            processing_ms = int((time.time() - start_time) * 1000)
            
            # Parse results
            detections = []
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is None or len(result.boxes) == 0:
                    logger.info("No objects detected")
                    return detections, processing_ms
                
                boxes = result.boxes
                
                for i, box in enumerate(boxes):
                    try:
                        class_id = int(box.cls[0]) if box.cls is not None else 0
                        label = result.names.get(class_id, f"Class {class_id}")
                        confidence = float(box.conf[0]) if box.conf is not None else 0.0
                        
                        detection = {
                            "class_id": class_id,
                            "label": label,
                            "confidence": confidence,
                            "bbox": {
                                "x1": float(box.xyxy[0][0]),
                                "y1": float(box.xyxy[0][1]),
                                "x2": float(box.xyxy[0][2]),
                                "y2": float(box.xyxy[0][3]),
                            },
                        }
                        detections.append(detection)
                    except (IndexError, TypeError, AttributeError) as e:
                        logger.warning(f"Error parsing detection {i}: {str(e)}")
                        continue
            
            logger.info(f"Detected {len(detections)} objects in {processing_ms}ms")
            return detections, processing_ms
            
        except Exception as e:
            logger.error(f"Detection failed: {str(e)}")
            raise

    def detect_from_image_file(
        self,
        image_path: str,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
    ) -> Tuple[List[dict], np.ndarray, int]:
        """
        Detect objects from image file.
        
        Returns:
            Tuple of (detections, annotated image array, processing time)
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to read image from {image_path}")
            
            # Run detection
            detections, processing_ms = self.detect_objects(
                image,
                confidence_threshold,
                iou_threshold,
            )
            
            # Annotate image
            annotated = self.draw_detections(image, detections)
            
            return detections, annotated, processing_ms
            
        except Exception as e:
            logger.error(f"Image detection failed: {str(e)}")
            raise

    def detect_from_video_file(
        self,
        video_path: str,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        frame_skip: int = 1,
    ) -> Tuple[str, List[dict], int]:
        """
        Detect objects from video file and create annotated output video.
        
        Returns:
            Tuple of (output video path, all detections, total processing time)
        """
        try:
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Failed to open video {video_path}")
            
            # Get video properties
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Setup video writer
            output_path = video_path.replace(".mp4", "_detected.mp4").replace(".avi", "_detected.avi")
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not writer.isOpened():
                logger.warning(f"Could not create video writer, trying with different codec")
                fourcc = cv2.VideoWriter_fourcc(*"MJPG")
                writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            total_time = 0
            frame_count = 0
            all_detections = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Skip frames if specified
                if (frame_count - 1) % frame_skip != 0:
                    if writer.isOpened():
                        writer.write(frame)
                    continue
                
                try:
                    # Run detection
                    detections, processing_ms = self.detect_objects(
                        frame,
                        confidence_threshold,
                        iou_threshold,
                    )
                    total_time += processing_ms
                    all_detections.extend(detections)
                    
                    # Annotate and write frame
                    annotated = self.draw_detections(frame, detections)
                    if writer.isOpened():
                        writer.write(annotated)
                except Exception as e:
                    logger.warning(f"Error processing frame {frame_count}: {str(e)}")
                    if writer.isOpened():
                        writer.write(frame)
            
            cap.release()
            writer.release()
            
            logger.info(f"Video processed: {frame_count} frames, {len(all_detections)} detections, {total_time}ms total")
            return output_path, all_detections, total_time
            
        except Exception as e:
            logger.error(f"Video detection failed: {str(e)}")
            raise

    def draw_detections(
        self,
        image: np.ndarray,
        detections: List[dict],
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels on image.
        
        Args:
            image: Input image array
            detections: List of detection dictionaries
            
        Returns:
            Annotated image array
        """
        if image is None or len(detections) == 0:
            return image
        
        annotated = image.copy()
        
        for detection in detections:
            try:
                bbox = detection.get("bbox", {})
                x1, y1 = int(bbox.get("x1", 0)), int(bbox.get("y1", 0))
                x2, y2 = int(bbox.get("x2", 0)), int(bbox.get("y2", 0))
                confidence = detection.get("confidence", 0.0)
                label = detection.get("label", "Unknown")
                
                # Draw bounding box
                color = (0, 255, 0)  # Green
                thickness = 2
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
                
                # Draw label with confidence
                text = f"{label} {confidence:.2f}"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                font_thickness = 1
                text_color = (255, 255, 255)
                bg_color = (0, 128, 0)
                
                # Get text size
                text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
                
                # Draw background rectangle
                cv2.rectangle(
                    annotated,
                    (x1, y1 - text_size[1] - 4),
                    (x1 + text_size[0] + 4, y1),
                    bg_color,
                    -1,
                )
                
                # Put text
                cv2.putText(
                    annotated,
                    text,
                    (x1 + 2, y1 - 2),
                    font,
                    font_scale,
                    text_color,
                    font_thickness,
                )
            except Exception as e:
                logger.warning(f"Error drawing detection: {str(e)}")
                continue
        
        return annotated

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        if self._model is None:
            return {"status": "not loaded"}
        
        try:
            return {
                "model_name": getattr(self._model, 'model_name', 'YOLOv8'),
                "num_classes": len(self._model.names) if self._model.names else 0,
                "class_names": list(self._model.names.values()) if self._model.names else [],
                "device": str(self._device or "cpu"),
                "status": "ready",
            }
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return {"status": "error", "error": str(e)}
