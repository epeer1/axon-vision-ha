#!/usr/bin/env python3
"""
Integration tests for pipeline components.
Tests individual components before testing the full pipeline.
"""
import unittest
import sys
import time
from pathlib import Path
import threading

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.streamer.video_streamer import VideoStreamer
from components.detector.motion_detector import MotionDetector  
from components.display.video_display import VideoDisplay
from utils.centralized_logger import CentralizedLogger


class TestPipelineComponents(unittest.TestCase):
    """Test individual pipeline components."""
    
    def setUp(self):
        """Set up test environment."""
        self.video_path = "People - 6387.mp4"
        self.assertTrue(Path(self.video_path).exists(), "Test video file not found")
    
    def test_video_streamer_initialization(self):
        """Test that VideoStreamer can be initialized."""
        streamer = VideoStreamer(self.video_path)
        self.assertIsNotNone(streamer)
        self.assertEqual(str(streamer.video_path), self.video_path)
    
    def test_video_file_opening(self):
        """Test that video file can be opened."""
        streamer = VideoStreamer(self.video_path)
        success = streamer.open_video()
        self.assertTrue(success, "Failed to open video file")
        self.assertGreater(streamer.total_frames, 0)
        self.assertGreater(streamer.original_fps, 0)
        streamer.close_video()
    
    def test_motion_detector_initialization(self):
        """Test that MotionDetector can be initialized."""
        detector = MotionDetector()
        self.assertIsNotNone(detector)
        self.assertEqual(detector.threshold, 25)  # Default from basic_vmd.py
        self.assertEqual(detector.dilate_iterations, 2)  # Default from basic_vmd.py
    
    def test_video_display_initialization(self):
        """Test that VideoDisplay can be initialized."""
        display = VideoDisplay()
        self.assertIsNotNone(display)
        self.assertEqual(display.window_name, "Motion Detection Pipeline")
    
    def test_centralized_logger_initialization(self):
        """Test that CentralizedLogger can be initialized."""
        logger = CentralizedLogger("test_pipeline.log", console_output=False)
        self.assertIsNotNone(logger)
        self.assertEqual(str(logger.log_file), "test_pipeline.log")


class TestZMQCommunication(unittest.TestCase):
    """Test ZeroMQ communication layer."""
    
    def test_zmq_imports(self):
        """Test that ZMQ imports work correctly."""
        try:
            import zmq
            from communication.zmq_manager import ZMQManager, PipelineComm
            from communication.protocol import MessageProtocol, Endpoints
        except ImportError as e:
            self.fail(f"ZMQ imports failed: {e}")
    
    def test_zmq_socket_creation(self):
        """Test that ZMQ sockets can be created with our configuration."""
        import zmq
        from communication.zmq_manager import ZMQManager
        
        # Test socket creation without binding/connecting
        manager = ZMQManager(zmq.PUSH, "ipc://test_endpoint", bind=False)
        self.assertIsNotNone(manager)
        self.assertFalse(manager.is_connected)


if __name__ == "__main__":
    print("=" * 60)
    print("PIPELINE COMPONENT INTEGRATION TESTS")
    print("=" * 60)
    
    # Run the tests
    unittest.main(verbosity=2) 