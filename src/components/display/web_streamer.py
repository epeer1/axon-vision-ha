#!/usr/bin/env python3
"""
Web Streamer Component - Streams processed frames to web browser in real-time.
"""
import cv2
import time
import logging
import threading
from typing import Optional
from flask import Flask, Response, render_template_string
import io
import base64

from core.data_models import DetectionResult, SystemMessage
from communication.zmq_manager import ZMQManager, PipelineComm
from utils.centralized_logger import PipelineLogger


class WebStreamer:
    """Streams processed video frames to web browser via HTTP."""
    
    def __init__(self, port: int = 5000, host: str = "127.0.0.1"):
        """
        Initialize web streamer.
        
        Args:
            port: HTTP server port
            host: Server host address
        """
        self.port = port
        self.host = host
        self.app = Flask(__name__)
        self.app.logger.disabled = True  # Disable Flask logs
        
        # ZMQ Communication
        self.frame_receiver: Optional[ZMQManager] = None
        
        # Streaming state
        self.is_streaming = False
        self.current_frame = None
        self.current_frame_data = None
        self.frame_lock = threading.Lock()
        
        # Statistics
        self.frames_received = 0
        self.frames_streamed = 0
        self.start_time = 0.0
        
        # Threading
        self.receiver_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        self.logger = logging.getLogger("WebStreamer")
        self.pipeline_logger = PipelineLogger("WebStreamer")
        
        # Setup Flask routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask web routes."""
        
        @self.app.route('/')
        def index():
            """Main page with video stream."""
            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Video Processing Pipeline - Live Stream</title>
                <style>
                    body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; margin: 0; padding: 20px; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .video-container { text-align: center; margin: 20px 0; }
                    .video-stream { max-width: 100%; border: 2px solid #333; border-radius: 8px; }
                    .info-panel { background: #2a2a2a; padding: 15px; border-radius: 8px; margin: 20px 0; }
                    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
                    .stat-item { background: #3a3a3a; padding: 10px; border-radius: 5px; text-align: center; }
                    .stat-value { font-size: 24px; font-weight: bold; color: #4CAF50; }
                    .stat-label { font-size: 12px; color: #aaa; }
                    h1 { text-align: center; color: #4CAF50; }
                    .status { color: #4CAF50; font-weight: bold; }
                </style>
                <script>
                    function updateStats() {
                        fetch('/stats')
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('frames-received').textContent = data.frames_received;
                                document.getElementById('frames-streamed').textContent = data.frames_streamed;
                                document.getElementById('fps').textContent = data.fps.toFixed(1);
                                document.getElementById('uptime').textContent = data.uptime.toFixed(1) + 's';
                            })
                            .catch(error => console.log('Stats update failed'));
                    }
                    
                    setInterval(updateStats, 1000);  // Update every second
                    window.onload = updateStats;
                </script>
            </head>
            <body>
                <div class="container">
                    <h1>🎥 Video Processing Pipeline - Live Stream</h1>
                    
                    <div class="info-panel">
                        <div class="stats">
                            <div class="stat-item">
                                <div class="stat-value" id="frames-received">0</div>
                                <div class="stat-label">FRAMES RECEIVED</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="frames-streamed">0</div>
                                <div class="stat-label">FRAMES STREAMED</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="fps">0.0</div>
                                <div class="stat-label">FPS</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value" id="uptime">0.0s</div>
                                <div class="stat-label">UPTIME</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="video-container">
                        <img src="/video_feed" class="video-stream" alt="Live Video Stream">
                    </div>
                    
                    <div class="info-panel">
                        <p><span class="status">● LIVE</span> Real-time motion detection pipeline</p>
                        <p>🔄 Streamer → Detector → WebStreamer → Browser</p>
                        <p>📡 Streaming on http://{{ host }}:{{ port }}</p>
                    </div>
                </div>
            </body>
            </html>
            '''
            return render_template_string(html, host=self.host, port=self.port)
        
        @self.app.route('/video_feed')
        def video_feed():
            """Video streaming route."""
            return Response(self._generate_frames(),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/stats')
        def stats():
            """Get streaming statistics as JSON."""
            uptime = time.time() - self.start_time if self.start_time > 0 else 0
            fps = self.frames_streamed / uptime if uptime > 0 else 0
            
            return {
                'frames_received': self.frames_received,
                'frames_streamed': self.frames_streamed,
                'fps': fps,
                'uptime': uptime,
                'is_streaming': self.is_streaming
            }
    
    def _generate_frames(self):
        """Generate frames for HTTP streaming."""
        while True:
            with self.frame_lock:
                if self.current_frame_data is not None:
                    frame_data = self.current_frame_data
                    self.frames_streamed += 1
                else:
                    # Send a "waiting" frame if no data
                    frame_data = self._create_waiting_frame()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS max
    
    def _create_waiting_frame(self):
        """Create a waiting frame when no video data is available."""
        import numpy as np
        
        # Create a simple waiting frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (40, 40, 40)  # Dark gray background
        
        # Add text
        cv2.putText(frame, "Waiting for video pipeline...", (120, 220), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(frame, "Starting video processing...", (140, 260), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (180, 180, 180), 2)
        
        # Add a simple border
        cv2.rectangle(frame, (10, 10), (630, 470), (100, 100, 100), 2)
        
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buffer.tobytes()
    
    def setup_communication(self) -> bool:
        """Setup ZMQ communication to receive processed frames."""
        try:
            self.frame_receiver = PipelineComm.create_web_receiver()
            if not self.frame_receiver.start():
                self.logger.error("Failed to start frame receiver")
                return False
            
            self.logger.info("Communication setup complete")
            self.pipeline_logger.info("WebStreamer communication established")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup communication: {e}")
            return False
    
    def start_streaming(self) -> bool:
        """Start receiving frames and web server."""
        if self.is_streaming:
            self.logger.warning("Already streaming")
            return True
        
        if not self.setup_communication():
            return False
        
        # Reset state
        self.stop_event.clear()
        self.frames_received = 0
        self.frames_streamed = 0
        self.start_time = time.time()
        
        # Start frame receiver thread
        self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receiver_thread.start()
        
        self.is_streaming = True
        self.logger.info(f"WebStreamer started on http://{self.host}:{self.port}")
        self.pipeline_logger.info(f"Web streaming started on port {self.port}")
        
        # Start Flask server (blocking)
        try:
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        except Exception as e:
            self.logger.error(f"Web server failed: {e}")
            return False
        
        return True
    
    def stop_streaming(self):
        """Stop streaming and cleanup."""
        if not self.is_streaming:
            return
        
        self.logger.info("Stopping web streaming...")
        self.pipeline_logger.info("Web streaming stopped")
        self.stop_event.set()
        
        if self.receiver_thread and self.receiver_thread.is_alive():
            self.receiver_thread.join(timeout=2.0)
        
        self.is_streaming = False
        self._cleanup()
        self.logger.info("Web streaming stopped")
    
    def _receive_loop(self):
        """Main frame receiving loop (runs in separate thread)."""
        try:
            while not self.stop_event.is_set():
                # Receive detection result from pipeline
                message = self.frame_receiver.receive(timeout_ms=1000)
                if message is None:
                    continue
                
                if isinstance(message, DetectionResult):
                    # Convert frame to JPEG for web streaming
                    frame_with_detections = self._draw_detections(message)
                    _, buffer = cv2.imencode('.jpg', frame_with_detections, 
                                           [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    # Update current frame (thread-safe)
                    with self.frame_lock:
                        self.current_frame_data = buffer.tobytes()
                        self.frames_received += 1
                
                elif isinstance(message, SystemMessage) and message.message_type == "end_of_stream":
                    self.logger.info("End of stream received")
                    self.pipeline_logger.info("Video stream ended")
                    break
        
        except Exception as e:
            self.logger.error(f"Frame receiving error: {e}")
            self.pipeline_logger.error(f"Frame receiving failed: {e}")
    
    def _draw_detections(self, detection_result: DetectionResult) -> cv2.Mat:
        """Draw detection boxes and info on frame."""
        frame = detection_result.frame.copy()
        
        # Draw detection boxes
        for detection in detection_result.detections:
            x, y, w, h = detection.bbox
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw detection label
            label = f"Motion: {detection.confidence:.2f}"
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Draw timestamp and stats
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        fps_text = f"FPS: {detection_result.processing_time:.1f}ms | Frame: {detection_result.frame_id}"
        cv2.putText(frame, fps_text, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        detection_text = f"Detections: {len(detection_result.detections)}"
        cv2.putText(frame, detection_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        return frame
    
    def _cleanup(self):
        """Cleanup resources."""
        if self.frame_receiver:
            self.frame_receiver.stop()
            self.frame_receiver = None
    
    def get_stats(self) -> dict:
        """Get streaming statistics."""
        uptime = time.time() - self.start_time if self.start_time > 0 else 0
        fps = self.frames_streamed / uptime if uptime > 0 else 0
        
        return {
            'frames_received': self.frames_received,
            'frames_streamed': self.frames_streamed,
            'fps': fps,
            'uptime': uptime,
            'is_streaming': self.is_streaming
        } 