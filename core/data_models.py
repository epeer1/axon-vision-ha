"""
Core data models for the video processing pipeline.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import time


@dataclass
class FrameData:
    """Represents a video frame with metadata."""
    frame_id: int
    timestamp: float
    frame: np.ndarray
    metadata: Dict[str, Any]
    
    @classmethod
    def create(cls, frame_id: int, frame: np.ndarray, metadata: Optional[Dict[str, Any]] = None):
        """Create a FrameData instance with current timestamp."""
        return cls(
            frame_id=frame_id,
            timestamp=time.time(),
            frame=frame,
            metadata=metadata or {}
        )


@dataclass
class Detection:
    """Represents a single motion detection."""
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    detection_type: str
    area: int
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get the center point of the detection."""
        x, y, w, h = self.bbox
        return (x + w // 2, y + h // 2)


@dataclass
class DetectionResult:
    """Complete detection result for a frame."""
    frame_id: int
    timestamp: float
    frame: np.ndarray
    detections: List[Detection]
    processing_time: float
    metadata: Dict[str, Any]
    
    @classmethod
    def create(cls, frame_data: FrameData, detections: List[Detection], 
               processing_time: float, metadata: Optional[Dict[str, Any]] = None):
        """Create a DetectionResult from FrameData and detections."""
        return cls(
            frame_id=frame_data.frame_id,
            timestamp=frame_data.timestamp,
            frame=frame_data.frame,
            detections=detections,
            processing_time=processing_time,
            metadata=metadata or {}
        )


@dataclass
class SystemMessage:
    """System control messages between processes."""
    message_type: str  # "shutdown", "pause", "resume", "status"
    payload: Dict[str, Any]
    timestamp: float
    
    @classmethod
    def shutdown(cls):
        """Create a shutdown message."""
        return cls(
            message_type="shutdown",
            payload={},
            timestamp=time.time()
        )
    
    @classmethod
    def status_request(cls):
        """Create a status request message."""
        return cls(
            message_type="status_request",
            payload={},
            timestamp=time.time()
        )


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    fps: float
    latency_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    queue_depth: int
    timestamp: float
    
    @classmethod
    def create(cls, fps: float, latency_ms: float, memory_usage_mb: float, 
               cpu_usage_percent: float, queue_depth: int):
        """Create performance metrics with current timestamp."""
        return cls(
            fps=fps,
            latency_ms=latency_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            queue_depth=queue_depth,
            timestamp=time.time()
        ) 