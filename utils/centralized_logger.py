"""
Centralized Logging Service - Collects logs from all pipeline components via ZMQ.
"""
import threading
import time
from pathlib import Path
from typing import Optional
import logging

from core.data_models import LogMessage, SystemMessage
from communication.zmq_manager import ZMQManager, PipelineComm


class CentralizedLogger:
    """Centralized logging service for the video processing pipeline."""
    
    def __init__(self, log_file: str = "pipeline.log", console_output: bool = True):
        """
        Initialize centralized logger.
        
        Args:
            log_file: Path to centralized log file
            console_output: Whether to also print logs to console
        """
        self.log_file = Path(log_file)
        self.console_output = console_output
        
        # ZMQ communication
        self.log_receiver: Optional[ZMQManager] = None
        
        # Threading
        self.logging_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.is_running = False
        
        # Statistics
        self.messages_logged = 0
        self.messages_by_level = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        self.messages_by_component = {}
        
        # Setup local logger for this service
        self.logger = logging.getLogger("CentralizedLogger")
        self.logger.setLevel(logging.INFO)
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def setup_communication(self) -> bool:
        """Setup ZMQ communication to receive log messages."""
        try:
            self.log_receiver = PipelineComm.create_log_receiver()
            if not self.log_receiver.start():
                self.logger.error("Failed to start log receiver")
                return False
            
            self.logger.info("Centralized logging communication setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup logging communication: {e}")
            return False
    
    def start_logging(self) -> bool:
        """Start the centralized logging service."""
        if self.is_running:
            self.logger.warning("Logging service already running")
            return True
        
        if not self.setup_communication():
            return False
        
        # Initialize log file with header
        self._write_log_header()
        
        # Reset statistics
        self.messages_logged = 0
        self.messages_by_level = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        self.messages_by_component.clear()
        
        # Start logging thread
        self.stop_event.clear()
        self.logging_thread = threading.Thread(target=self._logging_loop, daemon=True)
        self.logging_thread.start()
        
        self.is_running = True
        self.logger.info(f"Started centralized logging service (file: {self.log_file})")
        return True
    
    def stop_logging(self):
        """Stop the centralized logging service."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping centralized logging service...")
        self.stop_event.set()
        
        if self.logging_thread and self.logging_thread.is_alive():
            self.logging_thread.join(timeout=2.0)
        
        self.is_running = False
        self._write_log_footer()
        self._cleanup()
        self.logger.info("Centralized logging service stopped")
    
    def _logging_loop(self):
        """Main logging loop (runs in separate thread)."""
        try:
            while not self.stop_event.is_set():
                # Receive log message
                message = self.log_receiver.receive(timeout_ms=1000)
                
                if message is None:
                    continue  # Timeout - try again
                
                # Handle different message types
                if isinstance(message, SystemMessage):
                    if message.message_type == "end_of_stream":
                        self.logger.info("Received end-of-stream signal in logging service")
                        # Continue logging until explicitly stopped
                    continue
                
                if isinstance(message, LogMessage):
                    self._process_log_message(message)
        
        except Exception as e:
            self.logger.error(f"Logging loop error: {e}")
        
        finally:
            self.logger.info("Logging loop ended")
    
    def _process_log_message(self, log_msg: LogMessage):
        """Process and write a single log message."""
        try:
            # Format the message
            formatted_message = log_msg.format_message()
            
            # Write to file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(formatted_message + '\n')
                f.flush()  # Ensure immediate write
            
            # Optionally print to console
            if self.console_output:
                print(formatted_message)
            
            # Update statistics
            self.messages_logged += 1
            self.messages_by_level[log_msg.level] = self.messages_by_level.get(log_msg.level, 0) + 1
            self.messages_by_component[log_msg.component] = self.messages_by_component.get(log_msg.component, 0) + 1
            
        except Exception as e:
            self.logger.error(f"Failed to process log message: {e}")
    
    def _write_log_header(self):
        """Write header to log file."""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + '\n')
                f.write("VIDEO PROCESSING PIPELINE - CENTRALIZED LOG\n")
                f.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + '\n\n')
        except Exception as e:
            self.logger.error(f"Failed to write log header: {e}")
    
    def _write_log_footer(self):
        """Write footer with statistics to log file."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write('\n' + "=" * 80 + '\n')
                f.write("LOGGING SESSION SUMMARY\n")
                f.write(f"Ended: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total messages logged: {self.messages_logged}\n")
                f.write("Messages by level:\n")
                for level, count in self.messages_by_level.items():
                    if count > 0:
                        f.write(f"  {level}: {count}\n")
                f.write("Messages by component:\n")
                for component, count in self.messages_by_component.items():
                    f.write(f"  {component}: {count}\n")
                f.write("=" * 80 + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write log footer: {e}")
    
    def _cleanup(self):
        """Cleanup resources."""
        if self.log_receiver:
            self.log_receiver.stop()
            self.log_receiver = None
    
    def get_stats(self) -> dict:
        """Get logging statistics."""
        return {
            'is_running': self.is_running,
            'messages_logged': self.messages_logged,
            'messages_by_level': self.messages_by_level.copy(),
            'messages_by_component': self.messages_by_component.copy(),
            'log_file': str(self.log_file)
        }
    
    def __del__(self):
        """Destructor - ensure cleanup."""
        self.stop_logging()


class PipelineLogger:
    """Enhanced logger for pipeline components that sends to centralized logging."""
    
    def __init__(self, component_name: str):
        """Initialize pipeline logger for a specific component."""
        self.component_name = component_name
        self.log_sender: Optional[ZMQManager] = None
        self.local_logger = logging.getLogger(f"Pipeline-{component_name}")
        
        # Setup local fallback logging
        self.local_logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f'%(asctime)s [LOCAL] {component_name} %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        self.local_logger.addHandler(handler)
    
    def setup(self) -> bool:
        """Setup ZMQ connection to centralized logger."""
        try:
            self.log_sender = PipelineComm.create_log_sender()
            if not self.log_sender.start():
                self.local_logger.error("Failed to connect to centralized logger")
                return False
            return True
        except Exception as e:
            self.local_logger.error(f"Failed to setup centralized logging: {e}")
            return False
    
    def _send_log(self, level: str, message: str, frame_id: Optional[int] = None):
        """Send log message to centralized logger with local fallback."""
        try:
            # Send to centralized logger
            if self.log_sender:
                log_msg = LogMessage.create(level, self.component_name, message, frame_id)
                success = self.log_sender.send_log_message(log_msg, timeout_ms=100)
                if not success:
                    # Fallback to local logging
                    getattr(self.local_logger, level.lower())(f"[FALLBACK] {message}")
            else:
                # No centralized connection - use local only
                getattr(self.local_logger, level.lower())(message)
        except Exception as e:
            # Emergency fallback
            self.local_logger.error(f"Logging failed: {e} | Original message: {message}")
    
    def info(self, message: str, frame_id: Optional[int] = None):
        """Log info message."""
        self._send_log("INFO", message, frame_id)
    
    def warning(self, message: str, frame_id: Optional[int] = None):
        """Log warning message."""
        self._send_log("WARNING", message, frame_id)
    
    def error(self, message: str, frame_id: Optional[int] = None):
        """Log error message."""
        self._send_log("ERROR", message, frame_id)
    
    def debug(self, message: str, frame_id: Optional[int] = None):
        """Log debug message."""
        self._send_log("DEBUG", message, frame_id)
    
    def cleanup(self):
        """Cleanup logging resources."""
        if self.log_sender:
            self.log_sender.stop()
            self.log_sender = None 