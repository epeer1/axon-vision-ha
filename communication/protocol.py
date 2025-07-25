"""
Communication protocol definitions for the video processing pipeline.
"""
import json
import pickle
from typing import Any, Dict, Union
import numpy as np
from core.data_models import FrameData, DetectionResult, SystemMessage, PerformanceMetrics


class MessageProtocol:
    """Handles serialization/deserialization of messages for ZeroMQ."""
    
    # Message type identifiers
    FRAME_DATA = "frame_data"
    DETECTION_RESULT = "detection_result"
    SYSTEM_MESSAGE = "system_message"
    PERFORMANCE_METRICS = "performance_metrics"
    
    @staticmethod
    def serialize_frame_data(frame_data: FrameData) -> bytes:
        """Serialize FrameData for transmission."""
        # Use pickle for numpy arrays
        return pickle.dumps({
            'type': MessageProtocol.FRAME_DATA,
            'frame_id': frame_data.frame_id,
            'timestamp': frame_data.timestamp,
            'frame': frame_data.frame,
            'metadata': frame_data.metadata
        })
    
    @staticmethod
    def serialize_detection_result(result: DetectionResult) -> bytes:
        """Serialize DetectionResult for transmission."""
        detections_data = []
        for detection in result.detections:
            detections_data.append({
                'bbox': detection.bbox,
                'confidence': detection.confidence,
                'detection_type': detection.detection_type,
                'area': detection.area
            })
        
        return pickle.dumps({
            'type': MessageProtocol.DETECTION_RESULT,
            'frame_id': result.frame_id,
            'timestamp': result.timestamp,
            'frame': result.frame,
            'detections': detections_data,
            'processing_time': result.processing_time,
            'metadata': result.metadata
        })
    
    @staticmethod
    def serialize_system_message(message: SystemMessage) -> bytes:
        """Serialize SystemMessage for transmission."""
        data = {
            'type': MessageProtocol.SYSTEM_MESSAGE,
            'message_type': message.message_type,
            'payload': message.payload,
            'timestamp': message.timestamp
        }
        return json.dumps(data).encode('utf-8')
    
    @staticmethod
    def serialize_performance_metrics(metrics: PerformanceMetrics) -> bytes:
        """Serialize PerformanceMetrics for transmission."""
        data = {
            'type': MessageProtocol.PERFORMANCE_METRICS,
            'fps': metrics.fps,
            'latency_ms': metrics.latency_ms,
            'memory_usage_mb': metrics.memory_usage_mb,
            'cpu_usage_percent': metrics.cpu_usage_percent,
            'queue_depth': metrics.queue_depth,
            'timestamp': metrics.timestamp
        }
        return json.dumps(data).encode('utf-8')
    
    @staticmethod
    def deserialize(data: bytes) -> Union[FrameData, DetectionResult, SystemMessage, PerformanceMetrics]:
        """Deserialize received data based on message type."""
        try:
            # Try JSON first (for system messages and performance metrics)
            try:
                json_data = json.loads(data.decode('utf-8'))
                if json_data.get('type') == MessageProtocol.SYSTEM_MESSAGE:
                    return SystemMessage(
                        message_type=json_data['message_type'],
                        payload=json_data['payload'],
                        timestamp=json_data['timestamp']
                    )
                elif json_data.get('type') == MessageProtocol.PERFORMANCE_METRICS:
                    return PerformanceMetrics(
                        fps=json_data['fps'],
                        latency_ms=json_data['latency_ms'],
                        memory_usage_mb=json_data['memory_usage_mb'],
                        cpu_usage_percent=json_data['cpu_usage_percent'],
                        queue_depth=json_data['queue_depth'],
                        timestamp=json_data['timestamp']
                    )
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            
            # Use pickle for other message types
            obj_data = pickle.loads(data)
            msg_type = obj_data.get('type')
            
            if msg_type == MessageProtocol.FRAME_DATA:
                return FrameData(
                    frame_id=obj_data['frame_id'],
                    timestamp=obj_data['timestamp'],
                    frame=obj_data['frame'],
                    metadata=obj_data['metadata']
                )
            
            elif msg_type == MessageProtocol.DETECTION_RESULT:
                from core.data_models import Detection
                detections = []
                for det_data in obj_data['detections']:
                    detections.append(Detection(
                        bbox=det_data['bbox'],
                        confidence=det_data['confidence'],
                        detection_type=det_data['detection_type'],
                        area=det_data['area']
                    ))
                
                return DetectionResult(
                    frame_id=obj_data['frame_id'],
                    timestamp=obj_data['timestamp'],
                    frame=obj_data['frame'],
                    detections=detections,
                    processing_time=obj_data['processing_time'],
                    metadata=obj_data['metadata']
                )
            
            else:
                raise ValueError(f"Unknown message type: {msg_type}")
                
        except Exception as e:
            raise ValueError(f"Failed to deserialize message: {e}")


# ZeroMQ IPC endpoint configurations
class Endpoints:
    """Standard IPC endpoint assignments for pipeline communication."""
    STREAMER_TO_DETECTOR = "ipc://streamer_detector"
    DETECTOR_TO_DISPLAY = "ipc://detector_display"
    CONTROL_CHANNEL = "ipc://control_channel"
    MONITORING_CHANNEL = "ipc://monitoring_channel" 