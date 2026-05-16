import gradio as gr
import requests
import numpy as np
import cv2
from typing import Tuple, List
import os
from datetime import datetime
import time
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration from environment
API_PORT = os.getenv("API_PORT", "8000")
API_URL = f"http://localhost:{API_PORT}/api"
GRADIO_PORT = int(os.getenv("GRADIO_PORT", "7860"))
GRADIO_HOST = os.getenv("GRADIO_HOST", "0.0.0.0")


class DetectionApp:
    """Gradio application for real-time object detection."""

    def __init__(self):
        self.api_url = API_URL
        self.model_id = 1
        self.detection_history = []
        self.max_retries = 3
        self.request_timeout = 30

    def _check_api_connection(self) -> bool:
        """Check if API is accessible."""
        try:
            response = requests.get(f"{self.api_url.replace('/api', '')}/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"⚠️ API connection failed: {str(e)}")
            return False

    def detect_image(
        self,
        image: np.ndarray,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
    ) -> Tuple[np.ndarray, str]:
        """
        Detect objects in image.
        
        Args:
            image: Input image as numpy array
            confidence_threshold: Detection confidence threshold
            iou_threshold: IOU threshold for NMS
            
        Returns:
            Tuple of (annotated image, detection info text)
        """
        try:
            if image is None:
                return None, "❌ No image provided"
            
            # Check API connectivity
            if not self._check_api_connection():
                return None, f"❌ Cannot connect to API at {self.api_url}\n\nMake sure the FastAPI backend is running on http://localhost:8000"
            
            # Convert PIL to OpenCV format
            if isinstance(image, np.ndarray):
                frame = image
            else:
                frame = np.array(image)
                if len(frame.shape) == 3 and frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            
            # Validate image
            if frame is None or frame.size == 0:
                return None, "❌ Invalid image format"
            
            # Convert to bytes and send to API
            success, encoded = cv2.imencode(".jpg", frame)
            if not success:
                return None, "❌ Failed to encode image"
            
            image_bytes = encoded.tobytes()
            
            # Validate thresholds
            confidence_threshold = max(0.0, min(1.0, confidence_threshold))
            iou_threshold = max(0.0, min(1.0, iou_threshold))
            
            # Make API request
            files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
            params = {
                "confidence_threshold": confidence_threshold,
                "iou_threshold": iou_threshold,
                "model_id": self.model_id,
            }
            
            response = requests.post(
                f"{self.api_url}/detect/image",
                files=files,
                params=params,
                timeout=self.request_timeout,
            )
            
            if response.status_code != 200:
                error_msg = response.json().get("detail", response.text) if response.text else "Unknown error"
                return None, f"❌ Detection failed: {error_msg}"
            
            result = response.json()
            
            # Draw bounding boxes on image
            annotated = frame.copy()
            detected_objects = result.get("detected_objects", [])
            
            for obj in detected_objects:
                try:
                    x1 = int(obj.get("bbox_x1", 0))
                    y1 = int(obj.get("bbox_y1", 0))
                    x2 = int(obj.get("bbox_x2", 0))
                    y2 = int(obj.get("bbox_y2", 0))
                    label = obj.get("label", "Unknown")
                    confidence = float(obj.get("confidence", 0.0))
                    
                    # Draw bounding box
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Draw label with confidence
                    text = f"{label} {confidence:.2f}"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                    cv2.rectangle(
                        annotated,
                        (x1, y1 - text_size[1] - 4),
                        (x1 + text_size[0] + 4, y1),
                        (0, 128, 0),
                        -1,
                    )
                    cv2.putText(
                        annotated,
                        text,
                        (x1 + 2, y1 - 2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        1,
                    )
                except Exception as e:
                    print(f"⚠️ Error drawing detection: {str(e)}")
                    continue
            
            # Generate info text
            total_objects = len(detected_objects)
            processing_ms = result.get("processing_ms", 0)
            info_text = f"✅ **Detected {total_objects} objects in {processing_ms}ms**\n\n"
            
            if detected_objects:
                info_text += "**Detections:**\n"
                for i, obj in enumerate(detected_objects, 1):
                    conf = float(obj.get("confidence", 0.0))
                    info_text += f"  {i}. {obj.get('label', 'Unknown')} (Confidence: {conf:.1%})\n"
            else:
                info_text += "No objects detected"
            
            # Convert back to RGB for Gradio
            annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            
            return annotated_rgb, info_text
            
        except requests.exceptions.Timeout:
            return None, "❌ Request timeout - backend server may be slow or unresponsive"
        except requests.exceptions.ConnectionError as e:
            return None, f"❌ Connection error - cannot reach {self.api_url}\n\nMake sure the backend is running: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
        except Exception as e:
            return None, f"❌ Error: {str(e)}"

    def detect_video(
        self,
        video_path: str,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
    ) -> Tuple[str, str]:
        """
        Detect objects in video file.
        
        Args:
            video_path: Path to video file
            confidence_threshold: Detection confidence threshold
            iou_threshold: IOU threshold for NMS
            
        Returns:
            Tuple of (output video path, info text)
        """
        try:
            if not video_path or not os.path.exists(video_path):
                return None, "❌ No video provided or file not found"
            
            # Check API connectivity
            if not self._check_api_connection():
                return None, f"❌ Cannot connect to API at {self.api_url}"
            
            # Validate thresholds
            confidence_threshold = max(0.0, min(1.0, confidence_threshold))
            iou_threshold = max(0.0, min(1.0, iou_threshold))
            
            with open(video_path, "rb") as f:
                files = {"file": (os.path.basename(video_path), f, "video/mp4")}
                params = {
                    "confidence_threshold": confidence_threshold,
                    "iou_threshold": iou_threshold,
                    "model_id": self.model_id,
                }
                
                response = requests.post(
                    f"{self.api_url}/detect/video",
                    files=files,
                    params=params,
                    timeout=300,  # 5 minutes for videos
                )
            
            if response.status_code != 200:
                error_msg = response.json().get("detail", response.text) if response.text else "Unknown error"
                return None, f"❌ Detection failed: {error_msg}"
            
            result = response.json()
            output_video = result.get("output_video", "")
            total_objects = result.get("total_objects", 0)
            processing_ms = result.get("processing_ms", 0)
            
            info_text = f"""✅ **Video Processing Complete**

**Results:**
- Total Objects Detected: {total_objects}
- Processing Time: {processing_ms}ms
- Output Video: {os.path.basename(output_video) if output_video else 'N/A'}"""
            
            return output_video, info_text
            
        except requests.exceptions.Timeout:
            return None, "❌ Video processing timeout - video may be too large"
        except requests.exceptions.ConnectionError:
            return None, "❌ Connection error - backend server not responding"
        except Exception as e:
            return None, f"❌ Error: {str(e)}"

    def get_model_info(self) -> str:
        """Get information about the loaded model."""
        try:
            response = requests.get(
                f"{self.api_url}/detect/model-info",
                timeout=5
            )
            if response.status_code == 200:
                info = response.json()
                text = f"""**Model Information**

- **Model Name:** {info.get('model_name', 'N/A')}
- **Number of Classes:** {info.get('num_classes', 0)}
- **Device:** {info.get('device', 'N/A')}
- **Status:** {info.get('status', 'unknown')}

**Classes:** (showing first 20 of {len(info.get('class_names', []))})
"""
                classes = info.get('class_names', [])
                for i, cls in enumerate(classes[:20], 1):
                    text += f"  {i}. {cls}\n"
                if len(classes) > 20:
                    text += f"\n  ... and {len(classes) - 20} more classes"
                
                return text
            else:
                return f"❌ Failed to fetch model info: {response.status_code}"
        except requests.exceptions.Timeout:
            return "❌ Request timeout - backend taking too long"
        except requests.exceptions.ConnectionError:
            return f"❌ Cannot connect to backend at {self.api_url}"
        except Exception as e:
            return f"❌ Error fetching model info: {str(e)}"

    def get_statistics(self, days: int = 7) -> str:
        """Get detection statistics."""
        try:
            response = requests.get(
                f"{self.api_url}/logs/stats",
                params={"days": days},
                timeout=5,
            )
            
            if response.status_code == 200:
                stats = response.json()
                avg_conf = float(stats.get('average_confidence', 0.0))
                avg_time = float(stats.get('processing_time_avg_ms', 0.0))
                
                text = f"""**Detection Statistics (Last {days} days)**

- **Total Detections:** {stats.get('total_detections', 0)}
- **Total Objects Detected:** {stats.get('total_objects', 0)}
- **Average Confidence:** {avg_conf:.3f}
- **Most Common Class:** {stats.get('most_common_class', 'N/A')}
- **Avg Processing Time:** {avg_time:.2f}ms"""
                
                return text
            else:
                return f"❌ Failed to fetch statistics: {response.status_code}"
        except requests.exceptions.Timeout:
            return "❌ Request timeout"
        except requests.exceptions.ConnectionError:
            return "❌ Cannot connect to backend"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def get_detection_logs(self, skip: int = 0, limit: int = 10) -> pd.DataFrame:
        """Get detection logs as DataFrame."""
        try:
            response = requests.get(
                f"{self.api_url}/logs/detections",
                params={"skip": skip, "limit": limit},
                timeout=5,
            )
            
            if response.status_code == 200:
                detections = response.json()
                if not detections:
                    return pd.DataFrame(columns=["Filename", "Type", "Objects", "Time (ms)", "Date"])
                
                data = []
                for det in detections:
                    data.append({
                        "Filename": det.get('filename', 'N/A'),
                        "Type": det.get('input_type', 'unknown'),
                        "Objects": det.get('total_objects', 0),
                        "Time (ms)": det.get('processing_ms', 0),
                        "Date": det.get('created_at', 'N/A')[:19],
                    })
                
                return pd.DataFrame(data)
            else:
                return pd.DataFrame(columns=["Error"])
        except Exception as e:
            return pd.DataFrame({"Error": [str(e)]})

    def get_class_distribution(self, days: int = 7) -> Tuple[pd.DataFrame, str]:
        """Get class distribution chart data."""
        try:
            response = requests.get(
                f"{self.api_url}/logs/class-distribution",
                params={"days": days},
                timeout=5,
            )
            
            if response.status_code == 200:
                data = response.json()
                distribution = data.get('distribution', {})
                total = data.get('total_objects', 0)
                
                if not distribution:
                    return pd.DataFrame(columns=['Class', 'Count']), "No detections yet"
                
                # Create chart data
                df = pd.DataFrame(
                    list(distribution.items()),
                    columns=['Class', 'Count']
                ).sort_values('Count', ascending=False).head(15)
                
                info_text = f"**Total Objects (Last {days} days): {total}**\n\nShowing top 15 classes"
                
                return df, info_text
            else:
                return pd.DataFrame(columns=['Class', 'Count']), f"❌ Failed to fetch distribution: {response.status_code}"
        except requests.exceptions.Timeout:
            return pd.DataFrame(), "❌ Request timeout"
        except requests.exceptions.ConnectionError:
            return pd.DataFrame(), "❌ Cannot connect to backend"
        except Exception as e:
            return pd.DataFrame(), f"❌ Error: {str(e)}"


def create_interface():
    """Create Gradio interface."""
    app = DetectionApp()
    
    with gr.Blocks(title="Real-Time Object Detection", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🎯 Real-Time Object Detection with YOLOv8")
        gr.Markdown("Detect objects in images, videos, and webcam streams using YOLOv8")
        
        with gr.Tabs():
            # Image Detection Tab
            with gr.Tab("📷 Image Detection"):
                with gr.Row():
                    with gr.Column():
                        image_input = gr.Image(type="numpy", label="Upload Image")
                        conf_slider = gr.Slider(
                            0, 1, value=0.5,
                            label="Confidence Threshold",
                            info="Minimum confidence for detection"
                        )
                        iou_slider = gr.Slider(
                            0, 1, value=0.45,
                            label="IOU Threshold",
                            info="Intersection over Union threshold for NMS"
                        )
                        detect_btn = gr.Button("🔍 Detect Objects", variant="primary")
                    
                    with gr.Column():
                        image_output = gr.Image(label="Annotated Result")
                        info_output = gr.Markdown(label="Detection Results")
                
                detect_btn.click(
                    fn=app.detect_image,
                    inputs=[image_input, conf_slider, iou_slider],
                    outputs=[image_output, info_output],
                )
            
            # Video Detection Tab
            with gr.Tab("🎬 Video Detection"):
                with gr.Row():
                    with gr.Column():
                        video_input = gr.Video(label="Upload Video")
                        video_conf_slider = gr.Slider(
                            0, 1, value=0.5,
                            label="Confidence Threshold"
                        )
                        video_iou_slider = gr.Slider(
                            0, 1, value=0.45,
                            label="IOU Threshold"
                        )
                        video_detect_btn = gr.Button("▶️ Analyze Video", variant="primary")
                    
                    with gr.Column():
                        video_output = gr.Video(label="Annotated Video")
                        video_info = gr.Markdown(label="Processing Results")
                
                video_detect_btn.click(
                    fn=app.detect_video,
                    inputs=[video_input, video_conf_slider, video_iou_slider],
                    outputs=[video_output, video_info],
                )
            
            # Model Info Tab
            with gr.Tab("🧠 Model Information"):
                model_info_output = gr.Markdown()
                refresh_btn = gr.Button("🔄 Refresh Model Info", variant="secondary")
                
                refresh_btn.click(
                    fn=app.get_model_info,
                    outputs=model_info_output,
                )
                
                interface.load(
                    fn=app.get_model_info,
                    outputs=model_info_output,
                )
            
            # Statistics Tab
            with gr.Tab("📊 Statistics"):
                stats_days = gr.Slider(
                    1, 365, value=7,
                    label="Days",
                    info="Number of days to include in statistics",
                    step=1
                )
                stats_output = gr.Markdown()
                stats_btn = gr.Button("📈 Get Statistics", variant="secondary")
                
                stats_btn.click(
                    fn=app.get_statistics,
                    inputs=stats_days,
                    outputs=stats_output,
                )
                
                interface.load(
                    fn=app.get_statistics,
                    outputs=stats_output,
                )
            
            # Detection Logs Tab
            with gr.Tab("📋 Detection Logs"):
                logs_output = gr.Markdown()
                logs_refresh_btn = gr.Button("🔄 Refresh Logs", variant="secondary")
                
                logs_refresh_btn.click(
                    fn=app.get_detection_logs,
                    outputs=logs_output,
                )
                
                interface.load(
                    fn=app.get_detection_logs,
                    outputs=logs_output,
                )
            
            # Class Distribution Tab
            with gr.Tab("📊 Class Distribution"):
                dist_days = gr.Slider(
                    1, 365, value=7,
                    label="Days",
                    step=1
                )
                with gr.Row():
                    dist_chart = gr.BarPlot(
                        label="Object Class Distribution",
                        x="Class",
                        y="Count",
                        title="Detected Objects by Class"
                    )
                    dist_info = gr.Markdown()
                
                dist_btn = gr.Button("📊 Get Distribution", variant="secondary")
                
                dist_btn.click(
                    fn=app.get_class_distribution,
                    inputs=dist_days,
                    outputs=[dist_chart, dist_info],
                )
                
                interface.load(
                    fn=app.get_class_distribution,
                    outputs=[dist_chart, dist_info],
                )
        
        # Footer
        gr.Markdown("---")
        gr.Markdown(
            "🚀 **Real-Time Object Detection API** | "
            "[API Docs](http://localhost:8000/docs) | "
            "[GitHub](https://github.com/)"
        )
    
    return interface


if __name__ == "__main__":
    try:
        interface = create_interface()
        interface.launch(
            server_name=GRADIO_HOST,
            server_port=GRADIO_PORT,
            share=False,
            show_error=True,
        )
    except Exception as e:
        print(f"❌ Error starting Gradio app: {str(e)}")
        print("Make sure the FastAPI backend is running on http://localhost:8000")
        import traceback
        traceback.print_exc()
