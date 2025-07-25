"""
Video Streamer Component - Reads video files and streams frames to pipeline.
"""
import cv2
import time
import logging
import threading
from typing import Optional, Callable
from pathlib import Path

from core.data_models import FrameData, SystemMessage
from communication.zmq_manager import ZMQManager, PipelineComm


class VideoStreamer:
    """Streams video frames from file to the detection pipeline."""
    
    def __init__(self, video_path: str, target_fps: Optional[float] = None):
        """
        Initialize video streamer.
        
        Args:
            video_path: Path to video file
            target_fps: Target FPS (None = use original video FPS)
        """
        self.video_path = Path(video_path)
        self.target_fps = target_fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.sender: Optional[ZMQManager] = None
        
        # Video properties (set after opening)
        self.original_fps = 0.0
        self.total_frames = 0
        self.frame_width = 0
        self.frame_height = 0
        
        # Streaming state
        self.is_streaming = False
        self.is_paused = False
        self.current_frame_id = 0
        self.start_time = 0.0
        
        # Threading
        self.stream_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        self.logger = logging.getLogger("VideoStreamer")
    
    def open_video(self) -> bool:
        """Open video file and setup capture."""
        try:
            if not self.video_path.exists():
                self.logger.error(f"Video file not found: {self.video_path}")
                return False
            
            self.cap = cv2.VideoCapture(str(self.video_path))
            
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open video: {self.video_path}")
                return False
            
            # Get video properties
            self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Use original FPS if target not specified
            if self.target_fps is None:
                self.target_fps = self.original_fps
            
            self.logger.info(f"Opened video: {self.video_path}")
            self.logger.info(f"Properties: {self.frame_width}x{self.frame_height} @ {self.original_fps:.2f} FPS")
            self.logger.info(f"Total frames: {self.total_frames}, Duration: {self.total_frames/self.original_fps:.2f}s")
            self.logger.info(f"Streaming at: {self.target_fps:.2f} FPS")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to open video: {e}")
            return False
    
    def setup_communication(self) -> bool:
        """Setup ZMQ communication to detector."""
        try:
            self.sender = PipelineComm.create_streamer_sender()
            if not self.sender.start():
                self.logger.error("Failed to start ZMQ sender")
                return False
            
            self.logger.info("Communication setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup communication: {e}")
            return False
    
    def start_streaming(self) -> bool:
        """Start streaming video frames in a separate thread."""
        if self.is_streaming:
            self.logger.warning("Already streaming")
            return True
        
        if not self.open_video():
            return False
        
        if not self.setup_communication():
            self.close_video()
            return False
        
        # Reset state
        self.stop_event.clear()
        self.current_frame_id = 0
        self.is_paused = False
        
        # Start streaming thread
        self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.stream_thread.start()
        
        self.is_streaming = True
        self.logger.info("Started streaming")
        return True
    
    def stop_streaming(self):
        """Stop streaming and cleanup."""
        if not self.is_streaming:
            return
        
        self.logger.info("Stopping streaming...")
        self.stop_event.set()
        
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)
        
        self.is_streaming = False
        self._cleanup()
        self.logger.info("Streaming stopped")
    
    def pause_streaming(self):
        """Pause streaming (can be resumed)."""
        self.is_paused = True
        self.logger.info("Streaming paused")
    
    def resume_streaming(self):
        """Resume paused streaming."""
        self.is_paused = False
        self.logger.info("Streaming resumed")
    
    def _stream_loop(self):
        """Main streaming loop (runs in separate thread)."""
        frame_duration = 1.0 / self.target_fps  # Time between frames
        self.start_time = time.time()
        
        try:
            while not self.stop_event.is_set():
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                
                loop_start = time.time()
                
                # Read next frame
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.info("End of video reached")
                    self.is_streaming = False  # Mark streaming as done
                    break
                
                # Create FrameData
                frame_data = FrameData.create(
                    frame_id=self.current_frame_id,
                    frame=frame,
                    metadata={
                        'width': self.frame_width,
                        'height': self.frame_height,
                        'fps': self.target_fps,
                        'original_fps': self.original_fps,
                        'video_path': str(self.video_path)
                    }
                )
                
                # Send frame to detector
                success = self.sender.send_frame_data(frame_data, timeout_ms=500)
                if not success:
                    self.logger.warning(f"Failed to send frame {self.current_frame_id}")
                
                self.current_frame_id += 1
                
                # Frame rate control
                loop_time = time.time() - loop_start
                sleep_time = frame_duration - loop_time
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif sleep_time < -0.01:  # If we're more than 10ms behind
                    self.logger.debug(f"Frame processing taking too long: {loop_time:.3f}s")
        
        except Exception as e:
            self.logger.error(f"Streaming error: {e}")
        
        finally:
            # Send end-of-stream signal
            try:
                end_message = SystemMessage(
                    message_type="end_of_stream",
                    payload={'total_frames': self.current_frame_id},
                    timestamp=time.time()
                )
                self.sender.send_system_message(end_message)
                self.logger.info(f"Sent end-of-stream signal after {self.current_frame_id} frames")
            except Exception as e:
                self.logger.error(f"Failed to send end-of-stream: {e}")
    
    def _cleanup(self):
        """Cleanup resources."""
        self.close_video()
        if self.sender:
            self.sender.stop()
            self.sender = None
    
    def close_video(self):
        """Close video capture."""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def get_progress(self) -> dict:
        """Get streaming progress information."""
        if not self.is_streaming:
            return {'progress': 0.0, 'frame_id': 0, 'total_frames': 0}
        
        progress = (self.current_frame_id / self.total_frames) * 100 if self.total_frames > 0 else 0
        elapsed_time = time.time() - self.start_time if self.start_time > 0 else 0
        
        return {
            'progress': progress,
            'frame_id': self.current_frame_id,
            'total_frames': self.total_frames,
            'elapsed_time': elapsed_time,
            'fps': self.target_fps,
            'is_paused': self.is_paused
        }
    
    def __del__(self):
        """Destructor - ensure cleanup."""
        self.stop_streaming() 