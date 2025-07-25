# Video Processing Pipeline - Motion Detection System

A production-grade, multi-process video processing pipeline implementing real-time motion detection with OpenCV and ZeroMQ communication.

## 🏗️ Architecture Overview

```
┌─────────────┐  ZMQ/IPC  ┌─────────────┐  ZMQ/IPC  ┌─────────────┐
│   Streamer  │ ────────▶ │  Detector   │ ────────▶ │   Display   │
│   Process   │           │   Process   │           │   Process   │
└─────────────┘           └─────────────┘           └─────────────┘
      │                         │                         │
      └─────────────────────────┼─────────────────────────┘
                                ▼
                    ┌─────────────────────┐
                    │ Centralized Logging │
                    │      Service        │
                    └─────────────────────┘
```

## ✅ Features Implemented

### Phase A - Core Pipeline
- ✅ **Multi-process architecture** with separate video streaming, motion detection, and display processes
- ✅ **Real-time motion detection** using OpenCV frame differencing algorithm
- ✅ **Live video display** with detection bounding boxes and timestamps
- ✅ **ZeroMQ IPC communication** for high-performance inter-process messaging
- ✅ **Centralized logging** with file and console output
- ✅ **Professional error handling** and resource management

### Phase B Ready - Motion Blur
- ✅ **Motion blur toggle** available via `--blur-detections` flag
- ✅ **Gaussian blur** applied to detected motion areas

### Phase C Ready - Auto-Shutdown  
- ✅ **End-of-stream handling** with automatic pipeline shutdown
- ✅ **Graceful process termination** when video completes

## 🚀 Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
```

### Run Complete Pipeline

```bash
# Basic usage
python phase_a_runner.py "People - 6387.mp4"

# With motion blur (Phase B)
python phase_a_runner.py "People - 6387.mp4" --blur-detections

# Show logs after completion
python phase_a_runner.py "People - 6387.mp4" --show-logs
```

### Controls
- **ESC** - Stop video display
- **P** - Pause/resume video playback
- **Ctrl+C** - Stop entire pipeline

## 📁 Project Structure

```
AxonVisionHomeAssignment/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── ARCHITECTURE.md              # Detailed system architecture
├── assignment-description.md    # Original assignment requirements
│
├── # Phase Runners
├── phase_a_runner.py           # Complete pipeline orchestrator
│
├── # Process Executables  
├── logging_service.py          # Centralized logging service
├── streamer_process.py         # Video streaming process
├── detector_process.py         # Motion detection process
├── display_process.py          # Video display process
│
├── # Core Framework
├── core/
│   ├── data_models.py          # Pipeline data structures
├── communication/
│   ├── protocol.py             # ZMQ message serialization
│   └── zmq_manager.py          # ZMQ socket management
├── utils/
│   └── centralized_logger.py   # Logging infrastructure
│
├── # Pipeline Components
├── components/
│   ├── streamer/
│   │   └── video_streamer.py   # VideoStreamer class
│   ├── detector/
│   │   └── motion_detector.py  # MotionDetector class
│   └── display/
│       └── video_display.py    # VideoDisplay class
│
└── # Assets
    └── People - 6387.mp4       # Test video file
```

## 🔧 Individual Process Usage

### Centralized Logging Service
```bash
python logging_service.py [--log-file pipeline.log] [--no-console] [--verbose]
```

### Video Streamer Process
```bash
python streamer_process.py video_file [--fps 30] [--loop]
```

### Motion Detector Process
```bash
python detector_process.py [--threshold 25] [--min-area 500] [--dilate-iterations 2]
```

### Video Display Process
```bash
python display_process.py [--window-name "Pipeline"] [--blur-detections] [--no-fps]
```

## 📊 What You'll See

### Real-time Video Display
- **Green bounding boxes** around detected motion
- **Timestamp** in top-left corner with millisecond precision
- **FPS counter** showing real-time and average frame rates
- **Detection info** showing frame ID and detection count
- **Motion blur** on detected areas (when enabled)

### Terminal Output
```
================================================================================
VIDEO PROCESSING PIPELINE - PHASE A DEMONSTRATION  
================================================================================
Video file: People - 6387.mp4
Motion blur: Disabled
Python executable: C:\Python\python.exe
--------------------------------------------------------------------------------
Starting pipeline components...
  [1/4] Starting centralized logging service...
  [2/4] Starting display process...
  [3/4] Starting motion detector process...
  [4/4] Starting video streamer process...
--------------------------------------------------------------------------------
✅ ALL PIPELINE COMPONENTS STARTED SUCCESSFULLY!
```

### Centralized Logging (pipeline.log)
```
================================================================================
VIDEO PROCESSING PIPELINE - CENTRALIZED LOG
Started: 2024-01-15 14:32:10
================================================================================

14:32:11 INFO     Streamer    [Frame 0] | Started streaming People - 6387.mp4
14:32:11 INFO     Detector    [Frame 0] | First frame - storing as previous  
14:32:11 INFO     Display     [Frame 0] | Started video display
14:32:11 INFO     Detector    [Frame 5] | Found 2 motion detections
14:32:11 INFO     Display     [Frame 5] | Displayed frame with 2 detections
```

## 🧪 Technical Implementation

### Communication Architecture
- **ZeroMQ IPC sockets** for inter-process communication
- **Pickle serialization** for video frames and detection data
- **JSON serialization** for control messages and logs
- **Non-blocking operations** with configurable timeouts

### Motion Detection Algorithm
Based on the original `basic_vmd.py` with enhancements:
```python
# Frame differencing approach
gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
diff = cv2.absdiff(gray_frame, prev_frame)
thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
thresh = cv2.dilate(thresh, None, iterations=2)
contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
```

### Performance Optimizations
- **Threaded processing** in each component
- **Bounded message queues** to prevent memory overflow
- **FPS-controlled streaming** to maintain original video timing
- **Real-time performance monitoring** and statistics

## 🏷️ Git Workflow & Version Control

The project uses semantic commit messages and proper tagging:
```bash
git log --oneline
git tag                    # View phase tags
git show phase-a-v1.0     # View specific phase
```

## 🎯 Assignment Requirements Status

### ✅ Phase A Requirements
- [x] **Multi-process architecture** (Streamer, Detector, Display as separate processes)
- [x] **Motion detection** (OpenCV-based frame differencing)
- [x] **Real-time display** (cv2.imshow with smooth playback)
- [x] **Detection visualization** (green bounding boxes around motion)
- [x] **Timestamp overlay** (top-left corner with millisecond precision)
- [x] **Inter-process communication** (ZeroMQ IPC for production-grade messaging)

### ✅ Phase B Ready
- [x] **Motion blur capability** (Gaussian blur on detected regions)

### ✅ Phase C Ready  
- [x] **Auto-shutdown mechanism** (end-of-stream signal handling)

## 🏢 Production Considerations

This implementation demonstrates production-grade software engineering:

- **Scalable architecture** suitable for edge and cloud deployment
- **Robust error handling** with graceful degradation
- **Comprehensive logging** for debugging and monitoring
- **Performance optimization** for real-time processing
- **Resource management** with proper cleanup
- **Professional code structure** with clear separation of concerns

## 🤝 Contributing

The codebase follows professional Python standards:
- Type hints for better code documentation
- Comprehensive error handling
- Modular, testable architecture
- Clean commit history with semantic versioning

---

**Built for Axon Vision Home Assignment - Demonstrating production-ready video processing pipeline architecture** 