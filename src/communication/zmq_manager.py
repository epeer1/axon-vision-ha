"""
ZeroMQ manager for handling socket operations and message passing.
"""
import zmq
import logging
from typing import Optional, Union
import time

from .protocol import MessageProtocol, Endpoints
from core.data_models import FrameData, DetectionResult, SystemMessage, PerformanceMetrics, LogMessage


class ZMQManager:
    """Manages ZeroMQ sockets and message passing for the pipeline."""
    
    def __init__(self, socket_type: int, endpoint: str, bind: bool = False):
        """
        Initialize ZMQ manager.
        
        Args:
            socket_type: ZMQ socket type (zmq.PUSH, zmq.PULL, zmq.PUB, zmq.SUB)
            endpoint: IPC endpoint (e.g., "ipc://streamer_detector")  
            bind: True to bind (server), False to connect (client)
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(socket_type)
        self.endpoint = endpoint
        self.bind = bind
        self.is_connected = False
        
        # Configure socket options
        self.socket.setsockopt(zmq.LINGER, 0)     # Don't wait on close (immediate cleanup)
        self.socket.setsockopt(zmq.SNDHWM, 10)    # Send high water mark
        self.socket.setsockopt(zmq.RCVHWM, 10)    # Receive high water mark
        
        # Enable socket reuse for TCP (helps with TIME_WAIT issues)
        if endpoint.startswith("tcp://"):
            try:
                self.socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
                self.socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 1)
            except AttributeError:
                pass  # Some ZMQ versions don't have these options
        
        self.logger = logging.getLogger(f"ZMQManager-{endpoint}")
    
    def start(self) -> bool:
        """Start the socket (bind or connect)."""
        try:
            if self.bind:
                self.socket.bind(self.endpoint)
                self.logger.info(f"Bound to {self.endpoint}")
            else:
                self.socket.connect(self.endpoint)
                self.logger.info(f"Connected to {self.endpoint}")
            
            self.is_connected = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start socket: {e}")
            return False
    
    def stop(self):
        """Stop and cleanup the socket."""
        if self.is_connected:
            self.socket.close()
            self.context.term()
            self.is_connected = False
            self.logger.info(f"Stopped socket {self.endpoint}")
    
    def send_frame_data(self, frame_data: FrameData, timeout_ms: int = 1000) -> bool:
        """Send FrameData message."""
        if not self.is_connected:
            self.logger.error("Socket not connected")
            return False
        
        try:
            data = MessageProtocol.serialize_frame_data(frame_data)
            self.socket.send(data, zmq.NOBLOCK)
            return True
            
        except zmq.Again:
            self.logger.warning(f"Send timeout after {timeout_ms}ms")
            return False
        except Exception as e:
            self.logger.error(f"Send failed: {e}")
            return False
    
    def send_detection_result(self, result: DetectionResult, timeout_ms: int = 1000) -> bool:
        """Send DetectionResult message."""
        if not self.is_connected:
            self.logger.error("Socket not connected")
            return False
        
        try:
            data = MessageProtocol.serialize_detection_result(result)
            self.socket.send(data, zmq.NOBLOCK)
            return True
            
        except zmq.Again:
            self.logger.warning(f"Send timeout after {timeout_ms}ms")
            return False
        except Exception as e:
            self.logger.error(f"Send failed: {e}")
            return False
    
    def send_system_message(self, message: SystemMessage, timeout_ms: int = 1000) -> bool:
        """Send SystemMessage."""
        if not self.is_connected:
            self.logger.error("Socket not connected")
            return False
        
        try:
            data = MessageProtocol.serialize_system_message(message)
            self.socket.send(data, zmq.NOBLOCK)
            return True
            
        except zmq.Again:
            self.logger.warning(f"Send timeout after {timeout_ms}ms")
            return False
        except Exception as e:
            self.logger.error(f"Send failed: {e}")
            return False
    
    def send_performance_metrics(self, metrics: PerformanceMetrics, timeout_ms: int = 1000) -> bool:
        """Send PerformanceMetrics."""
        if not self.is_connected:
            self.logger.error("Socket not connected")
            return False
        
        try:
            data = MessageProtocol.serialize_performance_metrics(metrics)
            self.socket.send(data, zmq.NOBLOCK)
            return True
            
        except zmq.Again:
            self.logger.warning(f"Send timeout after {timeout_ms}ms")
            return False
        except Exception as e:
            self.logger.error(f"Send failed: {e}")
            return False
    
    def send_log_message(self, log_msg: LogMessage, timeout_ms: int = 1000) -> bool:
        """Send LogMessage."""
        if not self.is_connected:
            self.logger.error("Socket not connected")
            return False
        
        try:
            data = MessageProtocol.serialize_log_message(log_msg)
            self.socket.send(data, zmq.NOBLOCK)
            return True
            
        except zmq.Again:
            self.logger.warning(f"Send timeout after {timeout_ms}ms")
            return False
        except Exception as e:
            self.logger.error(f"Send failed: {e}")
            return False
    
    def receive(self, timeout_ms: int = 1000) -> Optional[Union[FrameData, DetectionResult, SystemMessage, PerformanceMetrics, LogMessage]]:
        """Receive and deserialize message."""
        if not self.is_connected:
            self.logger.error("Socket not connected")
            return None
        
        try:
            # Use poll to check for messages with timeout
            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLIN)
            
            if poller.poll(timeout_ms):
                data = self.socket.recv(zmq.NOBLOCK)
                return MessageProtocol.deserialize(data)
            else:
                # Timeout - no message available
                return None
                
        except zmq.Again:
            # No message available
            return None
        except Exception as e:
            self.logger.error(f"Receive failed: {e}")
            return None


class PipelineComm:
    """High-level communication helpers for pipeline components."""
    
    @staticmethod
    def create_streamer_sender() -> ZMQManager:
        """Create sender for Streamer → Detector communication."""
        return ZMQManager(
            socket_type=zmq.PUSH,
            endpoint=Endpoints.STREAMER_TO_DETECTOR,
            bind=True  # Streamer binds, Detector connects
        )
    
    @staticmethod
    def create_detector_receiver() -> ZMQManager:
        """Create receiver for Streamer → Detector communication."""
        return ZMQManager(
            socket_type=zmq.PULL,
            endpoint=Endpoints.STREAMER_TO_DETECTOR,
            bind=False  # Detector connects to Streamer
        )
    
    @staticmethod
    def create_detector_sender() -> ZMQManager:
        """Create sender for Detector → Display communication."""
        return ZMQManager(
            socket_type=zmq.PUSH,
            endpoint=Endpoints.DETECTOR_TO_DISPLAY,
            bind=True  # Detector binds, Display connects
        )
    
    @staticmethod
    def create_display_receiver() -> ZMQManager:
        """Create receiver for Detector → Display communication."""
        return ZMQManager(
            socket_type=zmq.PULL,
            endpoint=Endpoints.DETECTOR_TO_DISPLAY,
            bind=False  # Display connects to Detector
        )
    
    @staticmethod
    def create_display_sender() -> ZMQManager:
        """Create sender for Display → Web communication."""
        return ZMQManager(
            socket_type=zmq.PUSH,
            endpoint=Endpoints.DISPLAY_TO_WEB,
            bind=True  # Display binds, Web connects
        )
    
    @staticmethod
    def create_web_receiver() -> ZMQManager:
        """Create receiver for Display → Web communication."""
        return ZMQManager(
            socket_type=zmq.PULL,
            endpoint=Endpoints.DISPLAY_TO_WEB,
            bind=False  # Web connects to Display
        )
    
    @staticmethod
    def create_control_publisher() -> ZMQManager:
        """Create publisher for system control messages."""
        return ZMQManager(
            socket_type=zmq.PUB,
            endpoint=Endpoints.CONTROL_CHANNEL,
            bind=True
        )
    
    @staticmethod
    def create_control_subscriber() -> ZMQManager:
        """Create subscriber for system control messages."""
        manager = ZMQManager(
            socket_type=zmq.SUB,
            endpoint=Endpoints.CONTROL_CHANNEL,
            bind=False
        )
        # Subscribe to all control messages
        manager.socket.setsockopt(zmq.SUBSCRIBE, b"")
        return manager
    
    @staticmethod
    def create_log_sender() -> ZMQManager:
        """Create sender for centralized logging."""
        return ZMQManager(
            socket_type=zmq.PUSH,
            endpoint=Endpoints.LOGGING_CHANNEL,
            bind=False  # Components push to logging service
        )
    
    @staticmethod
    def create_log_receiver() -> ZMQManager:
        """Create receiver for centralized logging service."""
        return ZMQManager(
            socket_type=zmq.PULL,
            endpoint=Endpoints.LOGGING_CHANNEL,
            bind=True  # Logging service binds and receives
        ) 