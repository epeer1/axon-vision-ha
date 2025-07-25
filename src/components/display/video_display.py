"""
Video Display Component - Displays video with motion detection overlays.
Final component in the pipeline: receives DetectionResult from Detector and displays with cv2.imshow.
"""
import cv2
import numpy as np
import time
import threading
from typing import Optional, Tuple
from datetime import datetime

from core.data_models import DetectionResult, SystemMessage, LogMessage
from communication.zmq_manager import ZMQManager, PipelineComm
from utils.centralized_logger import PipelineLogger


class VideoDisplay:
    """Displays video frames with motion detection overlays and timestamp."""
    
    def __init__(self, window_name: str = "Motion Detection Pipeline", 
                 show_fps: bool = True, blur_detections: bool = False, show_window: bool = True):
        """
        Initialize video display.
        
        Args:
            window_name: OpenCV window name
            show_fps: Whether to show FPS counter
            blur_detections: Whether to blur detected areas (Phase B feature)
        """
        self.window_name = window_name
        self.show_fps = show_fps
        self.blur_detections = blur_detections
        self.show_window = show_window
        
        # Debug print
        print(f"[VideoDisplay] Initialized with blur_detections={blur_detections}")
        
        # ZMQ communication
        self.result_receiver: Optional[ZMQManager] = None
        self.web_sender: Optional[ZMQManager] = None  # Send to web streamer
        
        # Threading
        self.display_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.is_displaying = False
        
        # Display state
        self.current_frame_id = 0
        self.total_frames_displayed = 0
        self.total_detections_drawn = 0
        self.start_time = 0.0
        
        # FPS calculation
        self.fps_history = []
        self.last_frame_time = 0.0
        
        # Drawing parameters
        self.detection_color = (0, 255, 0)  # Green for motion boxes
        self.text_color = (255, 255, 255)   # White for text
        self.box_thickness = 2
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.7
        self.text_thickness = 2
        
        # Logging
        self.logger = PipelineLogger("Display")
    
    def setup_communication(self) -> bool:
        """Setup ZMQ communication to receive detection results."""
        try:
            self.result_receiver = PipelineComm.create_display_receiver()
            if not self.result_receiver.start():
                self.logger.error("Failed to start result receiver")
                return False
            
            # Setup web sender for forwarding processed frames
            self.web_sender = PipelineComm.create_display_sender()
            if not self.web_sender.start():
                self.logger.error("Failed to start web sender")
                return False
            
            self.logger.info("Communication setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup communication: {e}")
            return False
    
    def start_display(self) -> bool:
        """Start video display in a separate thread."""
        if self.is_displaying:
            self.logger.warning("Already displaying")
            return True
        
        # Setup logging first
        if not self.logger.setup():
            print("Warning: Failed to setup centralized logging, using local fallback")
        
        if not self.setup_communication():
            return False
        
        # Create OpenCV window only if needed
        if self.show_window:
            cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
            cv2.moveWindow(self.window_name, 100, 100)  # Position window
        
        # Reset state
        self.stop_event.clear()
        self.current_frame_id = 0
        self.total_frames_displayed = 0
        self.total_detections_drawn = 0
        self.start_time = time.time()
        self.fps_history.clear()
        self.last_frame_time = time.time()
        
        # Start display thread
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()
        
        self.is_displaying = True
        
        if self.show_window:
            self.logger.info(f"Started video display (window: {self.window_name})")
        else:
            self.logger.info("Started video display (forwarding mode - no window)")
        return True
    
    def stop_display(self):
        """Stop video display and cleanup."""
        if not self.is_displaying:
            return
        
        self.logger.info("Stopping video display...")
        self.stop_event.set()
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=2.0)
        
        self.is_displaying = False
        self._cleanup()
        self.logger.info("Video display stopped")
    
    def _display_loop(self):
        """Main display loop (runs in separate thread)."""
        try:
            while not self.stop_event.is_set():
                # Receive detection result from Detector
                message = self.result_receiver.receive(timeout_ms=1000)
                
                if message is None:
                    continue  # Timeout - try again
                
                # Handle different message types
                if isinstance(message, SystemMessage):
                    if message.message_type == "end_of_stream":
                        self.logger.info("Received end-of-stream signal - ending display")
                        # Forward end-of-stream to web streamer
                        if self.web_sender:
                            self.web_sender.send_system_message(message)
                            self.logger.info("Forwarded end-of-stream to web streamer")
                        break
                    continue
                
                if isinstance(message, DetectionResult):
                    # Process and optionally display the frame with detections
                    processed_frame = self._process_frame(message)
                    
                    # Update the message with processed frame before forwarding
                    if processed_frame is not None:
                        message.frame = processed_frame
                    
                    # Forward to web streamer
                    self._forward_to_web(message)
                    
                    # Display locally if window is enabled
                    if self.show_window:
                        cv2.imshow(self.window_name, processed_frame)
                        
                        # Check for user input (ESC to quit)
                        key = cv2.waitKey(1) & 0xFF
                        if key == 27:  # ESC key
                            self.logger.info("User pressed ESC - stopping display")
                            break
                        elif key == ord('p'):  # Pause toggle
                            self.logger.info("Display paused - press any key to continue")
                            cv2.waitKey(0)
                        self.logger.info("Display resumed")
        
        except Exception as e:
            self.logger.error(f"Display loop error: {e}")
        
        finally:
            self._display_summary()
    
    def _process_frame(self, result: DetectionResult):
        """Process a frame with detection overlays and return the processed frame."""
        try:
            frame = result.frame.copy()  # Work on copy to avoid modifying original
            self.current_frame_id = result.frame_id
            
            # Add timestamp (assignment requirement)
            self._add_timestamp(frame)
            
            # Always add blur indicator if blur is enabled
            if self.blur_detections:
                blur_text = "MOTION BLUR: ON"
                cv2.putText(frame, blur_text, (frame.shape[1]//2 - 100, 80), 
                           self.font, 1.0, (0, 0, 255), 3)
            
            # Draw detection boxes (assignment requirement)
            detections_drawn = self._draw_detections(frame, result.detections)
            self.total_detections_drawn += detections_drawn
            
            # Apply motion blur if enabled (Phase B feature)
            if self.blur_detections and result.detections:
                self.logger.info(f"Applying blur to {len(result.detections)} detections")
                frame = self._apply_motion_blur(frame, result.detections)
            else:
                if self.blur_detections:
                    self.logger.debug(f"Blur enabled but no detections in frame {result.frame_id}")
                else:
                    self.logger.debug("Blur not enabled")
            
            # Add FPS counter if enabled
            if self.show_fps:
                self._add_fps_counter(frame)
            
            # Add detection info
            self._add_detection_info(frame, result)
            
            # Add blur indicator if enabled
            if self.blur_detections and result.detections:
                self._add_blur_indicator(frame)
            
            # Update statistics
            self.total_frames_displayed += 1
            self._update_fps()
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Frame processing failed: {e}")
            return None
    
    def _forward_to_web(self, result: DetectionResult):
        """Forward processed frame to web streamer."""
        try:
            if self.web_sender:
                success = self.web_sender.send_detection_result(result, timeout_ms=100)
                if not success:
                    self.logger.debug("Web forward timeout")
        except Exception as e:
            self.logger.error(f"Web forwarding failed: {e}")
            self.total_frames_displayed += 1
            self._update_fps()
            
            # Log progress periodically
            if self.current_frame_id % 100 == 0:
                avg_fps = np.mean(self.fps_history[-30:]) if self.fps_history else 0
                self.logger.info(f"Displayed frame {self.current_frame_id}, "
                               f"FPS: {avg_fps:.1f}, "
                               f"detections: {len(result.detections)}", 
                               frame_id=self.current_frame_id)
        
        except Exception as e:
            self.logger.error(f"Failed to display frame {result.frame_id}: {e}", 
                            frame_id=result.frame_id)
    
    def _add_timestamp(self, frame: np.ndarray):
        """Add current timestamp to top-left corner (assignment requirement)."""
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Include milliseconds
        
        # Add background rectangle for better readability
        text_size = cv2.getTextSize(timestamp_str, self.font, self.font_scale, self.text_thickness)[0]
        cv2.rectangle(frame, (10, 10), (text_size[0] + 20, text_size[1] + 20), (0, 0, 0), -1)
        
        # Add timestamp text
        cv2.putText(frame, timestamp_str, (15, text_size[1] + 15), 
                   self.font, self.font_scale, self.text_color, self.text_thickness)
    
    def _draw_detections(self, frame: np.ndarray, detections) -> int:
        """Draw bounding boxes around detections (assignment requirement)."""
        detections_drawn = 0
        
        for detection in detections:
            x, y, w, h = detection.bbox
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), self.detection_color, self.box_thickness)
            
            # Add detection label with confidence
            label = f"Motion {detection.confidence:.2f}"
            label_size = cv2.getTextSize(label, self.font, self.font_scale * 0.8, self.text_thickness)[0]
            
            # Label background
            cv2.rectangle(frame, (x, y - label_size[1] - 10), 
                         (x + label_size[0], y), self.detection_color, -1)
            
            # Label text
            cv2.putText(frame, label, (x, y - 5), 
                       self.font, self.font_scale * 0.8, (0, 0, 0), self.text_thickness)
            
            detections_drawn += 1
        
        return detections_drawn
    
    def _apply_motion_blur(self, frame: np.ndarray, detections) -> np.ndarray:
        """Apply blur to detected motion areas (Phase B feature)."""
        for detection in detections:
            x, y, w, h = detection.bbox
            
            # Ensure coordinates are within frame bounds
            x = max(0, x)
            y = max(0, y)
            x_end = min(frame.shape[1], x + w)
            y_end = min(frame.shape[0], y + h)
            
            # Extract region
            region = frame[y:y_end, x:x_end].copy()
            
            if region.size > 0:  # Check if region is valid
                # Apply pixelation effect for very obvious blur
                pixel_size = 20
                # Ensure minimum size for resize
                new_w = max(1, w//pixel_size)
                new_h = max(1, h//pixel_size)
                temp = cv2.resize(region, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                pixelated = cv2.resize(temp, (region.shape[1], region.shape[0]), interpolation=cv2.INTER_NEAREST)
                
                # Replace region in frame
                frame[y:y_end, x:x_end] = pixelated
                
                # Add a red border around blurred area for debugging
                cv2.rectangle(frame, (x, y), (x_end, y_end), (0, 0, 255), 3)
        
        return frame
    
    def _add_fps_counter(self, frame: np.ndarray):
        """Add FPS counter to frame."""
        if self.fps_history:
            current_fps = self.fps_history[-1]
            avg_fps = np.mean(self.fps_history[-30:])  # 30-frame average
            
            fps_text = f"FPS: {current_fps:.1f} (avg: {avg_fps:.1f})"
            
            # Position in top-right
            text_size = cv2.getTextSize(fps_text, self.font, self.font_scale, self.text_thickness)[0]
            x = frame.shape[1] - text_size[0] - 15
            y = text_size[1] + 15
            
            # Background rectangle
            cv2.rectangle(frame, (x - 5, y - text_size[1] - 5), 
                         (x + text_size[0] + 5, y + 5), (0, 0, 0), -1)
            
            # FPS text
            cv2.putText(frame, fps_text, (x, y), 
                       self.font, self.font_scale, self.text_color, self.text_thickness)
    
    def _add_detection_info(self, frame: np.ndarray, result: DetectionResult):
        """Add detection information to frame."""
        info_text = f"Frame {result.frame_id} | Detections: {len(result.detections)}"
        
        # Position in bottom-left
        text_size = cv2.getTextSize(info_text, self.font, self.font_scale, self.text_thickness)[0]
        x = 15
        y = frame.shape[0] - 15
        
        # Background rectangle
        cv2.rectangle(frame, (x - 5, y - text_size[1] - 5), 
                     (x + text_size[0] + 5, y + 5), (0, 0, 0), -1)
        
        # Info text
        cv2.putText(frame, info_text, (x, y), 
                   self.font, self.font_scale, self.text_color, self.text_thickness)
    
    def _add_blur_indicator(self, frame: np.ndarray):
        """Add blur indicator to frame."""
        blur_text = "MOTION BLUR: ON"
        
        # Position in top-center
        text_size = cv2.getTextSize(blur_text, self.font, self.font_scale * 1.2, self.text_thickness + 1)[0]
        x = (frame.shape[1] - text_size[0]) // 2
        y = 50
        
        # Background rectangle with red color
        cv2.rectangle(frame, (x - 10, y - text_size[1] - 10), 
                     (x + text_size[0] + 10, y + 10), (0, 0, 255), -1)
        
        # Blur indicator text in white
        cv2.putText(frame, blur_text, (x, y), 
                   self.font, self.font_scale * 1.2, (255, 255, 255), self.text_thickness + 1)
    
    def _update_fps(self):
        """Update FPS calculation."""
        current_time = time.time()
        if self.last_frame_time > 0:
            frame_time = current_time - self.last_frame_time
            fps = 1.0 / frame_time if frame_time > 0 else 0
            self.fps_history.append(fps)
            
            # Keep only last 100 frames for FPS calculation
            if len(self.fps_history) > 100:
                self.fps_history.pop(0)
        
        self.last_frame_time = current_time
    
    def _display_summary(self):
        """Display session summary."""
        elapsed_time = time.time() - self.start_time
        avg_fps = np.mean(self.fps_history) if self.fps_history else 0
        
        self.logger.info(f"Display session summary:")
        self.logger.info(f"  Frames displayed: {self.total_frames_displayed}")
        self.logger.info(f"  Detections drawn: {self.total_detections_drawn}")
        self.logger.info(f"  Session duration: {elapsed_time:.1f}s")
        self.logger.info(f"  Average FPS: {avg_fps:.1f}")
    
    def _cleanup(self):
        """Cleanup resources."""
        if self.show_window:
            try:
                cv2.destroyWindow(self.window_name)
            except:
                pass
        
        if self.result_receiver:
            self.result_receiver.stop()
            self.result_receiver = None
        
        if self.web_sender:
            self.web_sender.stop()
            self.web_sender = None
        
        if self.logger:
            self.logger.cleanup()
    
    def get_stats(self) -> dict:
        """Get display statistics."""
        avg_fps = np.mean(self.fps_history) if self.fps_history else 0
        elapsed_time = time.time() - self.start_time if self.start_time > 0 else 0
        
        return {
            'is_displaying': self.is_displaying,
            'frames_displayed': self.total_frames_displayed,
            'detections_drawn': self.total_detections_drawn,
            'current_frame_id': self.current_frame_id,
            'average_fps': avg_fps,
            'elapsed_time': elapsed_time,
            'window_name': self.window_name
        }
    
    def __del__(self):
        """Destructor - ensure cleanup."""
        self.stop_display() 