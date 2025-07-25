"""
Motion Detector Component - Processes frames and detects motion using OpenCV.
Extracted and enhanced from basic_vmd.py with proper architecture.
"""
import cv2
import numpy as np
import time
import logging
import threading
from typing import Optional, List
import imutils

from core.data_models import FrameData, DetectionResult, Detection, SystemMessage
from communication.zmq_manager import ZMQManager, PipelineComm


class MotionDetector:
    """Detects motion in video frames using frame differencing approach."""
    
    def __init__(self, threshold: int = 25, min_area: int = 500, dilate_iterations: int = 2):
        """
        Initialize motion detector.
        
        Args:
            threshold: Threshold for binary image (from basic_vmd.py: 25)
            min_area: Minimum contour area to consider as motion
            dilate_iterations: Dilation iterations (from basic_vmd.py: 2)
        """
        # Detection parameters (from basic_vmd.py)
        self.threshold = threshold
        self.min_area = min_area
        self.dilate_iterations = dilate_iterations
        
        # Frame processing state
        self.prev_frame: Optional[np.ndarray] = None
        self.frame_counter = 0
        self.is_processing = False
        
        # ZMQ communication
        self.frame_receiver: Optional[ZMQManager] = None
        self.result_sender: Optional[ZMQManager] = None
        
        # Threading
        self.process_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Performance tracking
        self.total_detections = 0
        self.processing_times = []
        
        self.logger = logging.getLogger("MotionDetector")
    
    def setup_communication(self) -> bool:
        """Setup ZMQ communication for receiving frames and sending results."""
        try:
            # Receiver: Get frames from Streamer
            self.frame_receiver = PipelineComm.create_detector_receiver()
            if not self.frame_receiver.start():
                self.logger.error("Failed to start frame receiver")
                return False
            
            # Sender: Send results to Display
            self.result_sender = PipelineComm.create_detector_sender()
            if not self.result_sender.start():
                self.logger.error("Failed to start result sender")
                return False
            
            self.logger.info("Communication setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup communication: {e}")
            return False
    
    def start_detection(self) -> bool:
        """Start motion detection in a separate thread."""
        if self.is_processing:
            self.logger.warning("Already processing")
            return True
        
        if not self.setup_communication():
            return False
        
        # Reset state
        self.stop_event.clear()
        self.prev_frame = None
        self.frame_counter = 0
        self.total_detections = 0
        self.processing_times.clear()
        
        # Start processing thread
        self.process_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.process_thread.start()
        
        self.is_processing = True
        self.logger.info("Started motion detection")
        return True
    
    def stop_detection(self):
        """Stop motion detection and cleanup."""
        if not self.is_processing:
            return
        
        self.logger.info("Stopping detection...")
        self.stop_event.set()
        
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=2.0)
        
        self.is_processing = False
        self._cleanup()
        self.logger.info("Detection stopped")
    
    def _detection_loop(self):
        """Main detection loop (runs in separate thread)."""
        try:
            while not self.stop_event.is_set():
                # Receive frame from Streamer
                message = self.frame_receiver.receive(timeout_ms=1000)
                
                if message is None:
                    continue  # Timeout - try again
                
                # Handle different message types
                if isinstance(message, SystemMessage):
                    if message.message_type == "end_of_stream":
                        self.logger.info("Received end-of-stream signal")
                        break
                    continue
                
                if isinstance(message, FrameData):
                    # Process the frame
                    start_time = time.time()
                    detection_result = self._process_frame(message)
                    processing_time = (time.time() - start_time) * 1000  # Convert to ms
                    
                    if detection_result:
                        # Send result to Display
                        success = self.result_sender.send_detection_result(detection_result)
                        if not success:
                            self.logger.warning(f"Failed to send detection result for frame {message.frame_id}")
                        
                        # Track performance
                        self.processing_times.append(processing_time)
                        if len(detection_result.detections) > 0:
                            self.total_detections += len(detection_result.detections)
                    
                    # Log progress periodically
                    if self.frame_counter % 100 == 0:
                        avg_time = np.mean(self.processing_times[-100:]) if self.processing_times else 0
                        self.logger.info(f"Processed {self.frame_counter} frames, "
                                       f"avg processing: {avg_time:.1f}ms, "
                                       f"total detections: {self.total_detections}")
        
        except Exception as e:
            self.logger.error(f"Detection loop error: {e}")
        
        finally:
            # Forward end-of-stream signal to Display
            try:
                end_message = SystemMessage(
                    message_type="end_of_stream",
                    payload={
                        'total_frames_processed': self.frame_counter,
                        'total_detections': self.total_detections
                    },
                    timestamp=time.time()
                )
                self.result_sender.send_system_message(end_message)
                self.logger.info("Forwarded end-of-stream signal to Display")
            except Exception as e:
                self.logger.error(f"Failed to forward end-of-stream: {e}")
    
    def _process_frame(self, frame_data: FrameData) -> Optional[DetectionResult]:
        """
        Process a single frame for motion detection.
        This contains the core logic from basic_vmd.py, properly structured.
        """
        try:
            frame = frame_data.frame
            self.frame_counter += 1
            
            # Convert to grayscale (from basic_vmd.py)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            detections = []
            
            # First frame - just store as previous
            if self.prev_frame is None:
                self.prev_frame = gray_frame
                self.logger.debug(f"First frame {frame_data.frame_id} - storing as previous")
            else:
                # Motion detection algorithm (from basic_vmd.py)
                
                # 1. Frame difference
                diff = cv2.absdiff(gray_frame, self.prev_frame)
                
                # 2. Threshold (from basic_vmd.py: threshold=25)
                thresh = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)[1]
                
                # 3. Dilate to fill gaps (from basic_vmd.py: iterations=2)
                thresh = cv2.dilate(thresh, None, iterations=self.dilate_iterations)
                
                # 4. Find contours (from basic_vmd.py)
                cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)
                
                # 5. Convert contours to Detection objects
                for contour in cnts:
                    area = cv2.contourArea(contour)
                    
                    # Filter by minimum area
                    if area >= self.min_area:
                        # Get bounding box
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Calculate confidence based on area (larger = more confident)
                        confidence = min(1.0, area / 10000.0)  # Normalize to 0-1 range
                        
                        detection = Detection(
                            bbox=(x, y, w, h),
                            confidence=confidence,
                            detection_type="motion",
                            area=int(area)
                        )
                        detections.append(detection)
                
                # Update previous frame (from basic_vmd.py)
                self.prev_frame = gray_frame
            
            # Create detection result
            processing_time = 0  # Will be calculated by caller
            result = DetectionResult.create(
                frame_data=frame_data,
                detections=detections,
                processing_time=processing_time,
                metadata={
                    'detection_method': 'frame_difference',
                    'threshold': self.threshold,
                    'min_area': self.min_area,
                    'contours_found': len(detections)
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process frame {frame_data.frame_id}: {e}")
            return None
    
    def _cleanup(self):
        """Cleanup resources."""
        if self.frame_receiver:
            self.frame_receiver.stop()
            self.frame_receiver = None
        
        if self.result_sender:
            self.result_sender.stop()
            self.result_sender = None
    
    def get_stats(self) -> dict:
        """Get detection statistics."""
        avg_processing_time = np.mean(self.processing_times) if self.processing_times else 0
        
        return {
            'frames_processed': self.frame_counter,
            'total_detections': self.total_detections,
            'avg_processing_time_ms': avg_processing_time,
            'detections_per_frame': self.total_detections / max(1, self.frame_counter),
            'is_processing': self.is_processing
        }
    
    def __del__(self):
        """Destructor - ensure cleanup."""
        self.stop_detection() 