#!/usr/bin/env python3
"""
Basic test script to isolate issues before running full pipeline.
"""
import sys
from pathlib import Path

print("=" * 60)
print("BASIC SYSTEM TEST")
print("=" * 60)

# Test 1: Basic imports
print("1. Testing imports...")
try:
    import cv2
    print("  ✅ OpenCV imported successfully")
except ImportError as e:
    print(f"  ❌ OpenCV import failed: {e}")
    sys.exit(1)

try:
    import zmq
    print("  ✅ ZeroMQ imported successfully")
    print(f"     ZMQ version: {zmq.pyzmq_version()}")
except ImportError as e:
    print(f"  ❌ ZeroMQ import failed: {e}")
    sys.exit(1)

try:
    import imutils
    print("  ✅ imutils imported successfully")
except ImportError as e:
    print(f"  ❌ imutils import failed: {e}")
    sys.exit(1)

# Test 2: Video file access
print("\n2. Testing video file...")
video_path = Path("People - 6387.mp4")
if video_path.exists():
    print(f"  ✅ Video file found: {video_path}")
    print(f"     File size: {video_path.stat().st_size / (1024*1024):.1f} MB")
else:
    print(f"  ❌ Video file not found: {video_path}")
    print("     Current directory contents:")
    for item in Path(".").iterdir():
        if item.suffix in ['.mp4', '.avi', '.mov']:
            print(f"       - {item}")

# Test 3: OpenCV video reading
print("\n3. Testing OpenCV video reading...")
try:
    cap = cv2.VideoCapture(str(video_path))
    if cap.isOpened():
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"  ✅ Video opened successfully")
        print(f"     Resolution: {width}x{height}")
        print(f"     FPS: {fps}")
        print(f"     Frames: {frame_count}")
        print(f"     Duration: {frame_count/fps:.1f}s")
        
        # Try reading one frame
        ret, frame = cap.read()
        if ret:
            print(f"  ✅ Successfully read first frame")
            print(f"     Frame shape: {frame.shape}")
        else:
            print(f"  ❌ Failed to read first frame")
        
        cap.release()
    else:
        print(f"  ❌ Failed to open video file")
except Exception as e:
    print(f"  ❌ Error testing video: {e}")

# Test 4: ZMQ socket creation
print("\n4. Testing ZMQ socket creation...")
try:
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    
    # Test the socket options that were causing issues
    socket.setsockopt(zmq.LINGER, 1000)
    socket.setsockopt(zmq.SNDHWM, 10)
    socket.setsockopt(zmq.RCVHWM, 10)
    
    print("  ✅ ZMQ socket created and configured successfully")
    
    socket.close()
    context.term()
except Exception as e:
    print(f"  ❌ ZMQ socket test failed: {e}")

print("\n" + "=" * 60)
print("BASIC TEST COMPLETE")
print("=" * 60) 