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
- ✅ **ZeroMQ communication** with platform-adaptive transport (IPC on Linux, TCP on Windows)
- ✅ **Centralized logging** with file and console output
- ✅ **Professional error handling** and resource management

### Phase B - Motion Blur
- ✅ **Automatic motion blur** on detected areas (enabled by default in Phase B)
- ✅ **Pixelation effect** for clear visual feedback
- ✅ **Red "MOTION BLUR: ON" indicator** in video display
- ✅ **Toggle support** via `--no-blur` flag for comparison

### Phase C - Automatic Shutdown
- ✅ **Automatic pipeline shutdown** when video ends
- ✅ **Graceful cascade termination** of all processes
- ✅ **Clean resource cleanup** and proper exit codes
- ✅ **All Phase B features** included

## 🚀 Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
```

### Using Custom Video Files

The pipeline accepts any video file supported by OpenCV (mp4, avi, mov, etc.):

```bash
# Default video (included in repo)
python run_pipeline.py

# Custom video file - relative path
python run_pipeline.py "videos/my_video.mp4"

# Custom video file - absolute path
python run_pipeline.py "C:/Users/name/Videos/my_video.mp4"

# Custom video with specific phase
python run_pipeline.py "my_video.mp4" -p b

# For filenames with spaces, use quotes
python run_pipeline.py "My Video File.mp4" -p c
```

### Run Complete Pipeline

```bash
# Run Phase A (basic pipeline) - default
python run_pipeline.py

# Run Phase B (with motion blur)
python run_pipeline.py -p b

# Run Phase C (with automatic shutdown)
python run_pipeline.py -p c

# With specific video file
python run_pipeline.py "data/People - 6387.mp4" -p b

# Phase B without blur (for comparison)
python run_pipeline.py -p b --no-blur

# Phase A with blur enabled
python run_pipeline.py -p a --blur-detections

# Show logs after completion
python run_pipeline.py -p c --show-logs

# View all available options
python run_pipeline.py --help
```

### Direct Phase Runners

You can also run specific phases directly:

```bash
# Phase A
python src/phase_a_runner.py "data/People - 6387.mp4"

# Phase B
python src/phase_b_runner.py "data/People - 6387.mp4"

# Phase C
python src/phase_c_runner.py "data/People - 6387.mp4"
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
├── DESIGN_DECISIONS.md          # Comprehensive explanation of all choices
├── assignment-description.md    # Original assignment requirements
├── run_pipeline.py             # Unified runner script for all phases
│
├── data/                       # Video files
│   └── People - 6387.mp4       # Test video
│
├── src/                        # Source code
│   ├── phase_a_runner.py       # Complete pipeline orchestrator
│   │
│   ├── processes/              # Process entry points
│   │   ├── logging_service.py  # Centralized logging service
│   │   ├── streamer_process.py # Video streaming process
│   │   ├── detector_process.py # Motion detection process
│   │   ├── display_process.py  # Video display process
│   │   └── web_streamer_process.py # Web streaming process
│   │
│   ├── components/             # Pipeline components
│   │   ├── streamer/
│   │   │   └── video_streamer.py   # VideoStreamer class
│   │   ├── detector/
│   │   │   └── motion_detector.py  # MotionDetector class
│   │   └── display/
│   │       ├── video_display.py    # VideoDisplay class
│   │       └── web_streamer.py    # WebStreamer class
│   │
│   ├── core/                   # Core data structures
│   │   └── data_models.py      # Pipeline data structures
│   │
│   ├── communication/          # IPC/Network communication
│   │   ├── protocol.py         # ZMQ message serialization
│   │   └── zmq_manager.py      # ZMQ socket management
│   │
│   └── utils/                  # Utilities
│       └── centralized_logger.py # Logging infrastructure
│
├── examples/                   # Example code
│   └── basic_vmd.py           # Basic motion detection example
│
├── tests/                      # Test suite
│   ├── test_basic.py          # Basic functionality tests
│   └── test_pipeline_integration.py # Integration tests
│
└── docs/                       # Documentation
    └── _תרגיל תוכנה 2023.docx # Original assignment (Hebrew)
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

### ✅ Phase A - Core Pipeline
- [x] **Multi-process architecture** (Streamer, Detector, Display as separate processes)
- [x] **Motion detection** (OpenCV-based frame differencing)
- [x] **Real-time display** (cv2.imshow with smooth playback)
- [x] **Detection visualization** (green bounding boxes around motion)
- [x] **Timestamp overlay** (top-left corner with millisecond precision)
- [x] **Inter-process communication** (ZeroMQ IPC for production-grade messaging)

### ✅ Phase B - Motion Blur
- [x] **Motion blur on detections** (pixelation effect for clear visibility)
- [x] **Visual indicator** ("MOTION BLUR: ON" overlay when active)
- [x] **Toggle support** (--no-blur flag for easy comparison)
- [x] **All Phase A features preserved** (full backward compatibility)

### ✅ Phase C - Automatic Shutdown
- [x] **End-of-stream detection** (recognizes when video completes)
- [x] **Cascade shutdown** (orderly termination of all processes)
- [x] **Clean resource cleanup** (proper socket closing and thread joining)
- [x] **All Phase A+B features preserved** (complete functionality)

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and component details
- **[DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)** - Comprehensive explanation of all technical choices
- **[assignment-description.md](assignment-description.md)** - Original requirements

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