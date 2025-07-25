# Video Processing Pipeline - Architecture Design

## 🏗️ System Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Streamer  │───▶│  Detector   │───▶│   Display   │
│             │    │             │    │             │
│ - Read Video│    │ - Motion    │    │ - Draw      │
│ - Extract   │    │   Detection │    │ - Blur      │
│   Frames    │    │ - Analysis  │    │ - Show      │
└─────────────┘    └─────────────┘    └─────────────┘
      ▲                   ▲                   ▲
      │                   │                   │
   Process 1           Process 2           Process 3
```

## 📁 Repository Structure

```
AxonVisionHomeAssignment/
├── README.md                    # Project overview and usage
├── ARCHITECTURE.md              # This file - system design
├── DESIGN_DECISIONS.md          # Detailed explanation of choices
├── assignment-description.md    # Original requirements
├── requirements.txt             # Python dependencies
├── run_pipeline.py             # Unified runner for all phases
├── .gitignore                  # Git ignore rules
│
├── data/                       # Video files
│   └── People - 6387.mp4       # Test video
│
├── src/                        # Source code
│   ├── phase_a_runner.py       # Phase A orchestrator
│   ├── phase_b_runner.py       # Phase B orchestrator (with blur)
│   ├── phase_c_runner.py       # Phase C orchestrator (auto-shutdown)
│   │
│   ├── processes/              # Process entry points
│   │   ├── streamer_process.py # Video streaming process
│   │   ├── detector_process.py # Motion detection process
│   │   ├── display_process.py  # Video display process
│   │   ├── web_streamer_process.py # Web streaming process
│   │   └── logging_service.py  # Centralized logging
│   │
│   ├── components/             # Core components
│   │   ├── __init__.py
│   │   ├── streamer/
│   │   │   ├── __init__.py
│   │   │   └── video_streamer.py
│   │   ├── detector/
│   │   │   ├── __init__.py
│   │   │   └── motion_detector.py
│   │   └── display/
│   │       ├── __init__.py
│   │       ├── video_display.py
│   │       └── web_streamer.py
│   │
│   ├── communication/          # IPC/Network layer
│   │   ├── __init__.py
│   │   ├── protocol.py         # Message serialization
│   │   └── zmq_manager.py      # ZeroMQ socket management
│   │
│   ├── core/                   # Data models
│   │   ├── __init__.py
│   │   └── data_models.py
│   │
│   └── utils/                  # Utilities
│       ├── __init__.py
│       └── centralized_logger.py
│
├── examples/                   # Example code
│   └── basic_vmd.py           # Original motion detection
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_basic.py
│   └── test_pipeline_integration.py
│
└── docs/                       # Documentation
    └── _תרגיל תוכנה 2023.docx # Original assignment (Hebrew)
```

## 🔧 Component Architecture

### 1. Streamer Component
**Responsibilities:**
- Read video file frame by frame
- Control playback timing/FPS
- Send frames to Detector

**Interface:**
```python
class VideoStreamer:
    def __init__(self, video_path: str, target_fps: int)
    def start_streaming(self) -> None
    def stop_streaming(self) -> None
    def send_frame(self, frame: np.ndarray) -> bool
```

### 2. Detector Component
**Responsibilities:**
- Receive frames from Streamer
- Perform motion detection
- Send frame + detection data to Display

**Interface:**
```python
class MotionDetector:
    def __init__(self, detection_config: DetectionConfig)
    def process_frame(self, frame: np.ndarray) -> DetectionResult
    def start_detection(self) -> None
    def stop_detection(self) -> None
```

### 3. Display Component
**Responsibilities:**
- Receive frame + detection data
- Draw detections and timestamp
- Display video smoothly
- Handle blurring (Phase B)

**Interface:**
```python
class VideoDisplay:
    def __init__(self, display_config: DisplayConfig)
    def render_frame(self, frame: np.ndarray, detections: List[Detection]) -> None
    def add_timestamp(self, frame: np.ndarray) -> np.ndarray
    def apply_blur(self, frame: np.ndarray, regions: List[Region]) -> np.ndarray
```

## 🔄 Communication Strategy

### ⭐ **CHOSEN: ZeroMQ with Platform-Adaptive Transport**
- **Technology**: ZeroMQ with automatic transport selection
  - **IPC sockets** on Linux/Unix: `ipc://streamer_detector`, etc. (better performance)
  - **TCP sockets** on Windows: `tcp://127.0.0.1:5555`, etc. (IPC not supported)
- **Message Format**: Pickle protocol 5 with out-of-band buffers for numpy arrays
- **Pattern**: PUSH/PULL for unidirectional flow, PUB/SUB for broadcasts

#### Why ZeroMQ?
1. **Performance**: Zero-copy message passing, optimized for large binary data
2. **Reliability**: Automatic reconnection, message queuing, no data loss
3. **Flexibility**: Works identically across platforms (Windows/Linux/Mac)
4. **Industry Standard**: Used in production video processing systems
5. **Developer Experience**: Clean API, good documentation, active community

#### Implementation Details
- **Serialization**: Pickle protocol 5 for numpy array optimization
- **Socket Types**: 
  - PUSH/PULL for pipeline stages (guaranteed delivery)
  - PUB/SUB for logging service (fire-and-forget)
- **Error Handling**: Automatic reconnection with exponential backoff
- **Flow Control**: High water mark (HWM) set to prevent memory overflow

#### Platform Adaptation
- **Automatic Detection**: System detects platform and chooses optimal transport
- **Linux/Unix**: Uses IPC sockets for maximum performance
- **Windows**: Falls back to TCP (localhost) since IPC not supported
- **Override**: Set `FORCE_TCP=true` environment variable to force TCP on any platform
- **Same API**: Application code unchanged regardless of transport

For detailed explanation of all design choices, see [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md).

## 📊 Data Models

### Frame Data
```python
@dataclass
class FrameData:
    frame_id: int
    timestamp: float
    frame: np.ndarray
    metadata: Dict[str, Any]
```

### Detection Result
```python
@dataclass
class DetectionResult:
    frame_id: int
    timestamp: float
    frame: np.ndarray
    detections: List[Detection]
    processing_time: float

@dataclass
class Detection:
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    detection_type: str
```

## ⚡ Performance Considerations

### Timing & Synchronization
- **Frame Rate Control**: Maintain original video FPS
- **Buffer Management**: Prevent memory overflow with bounded queues
- **Backpressure**: Handle slow components gracefully

### Memory Optimization
- **Frame Sharing**: Use shared memory for large frames
- **Queue Size Limits**: Prevent unbounded memory growth
- **Garbage Collection**: Proper cleanup of processed frames

## 🔄 Phase Implementation Strategy

### Phase A: Core Pipeline
1. Implement basic IPC with queues
2. Create minimal viable components
3. Focus on smooth video playback
4. Basic motion detection integration

### Phase B: Motion Blur
1. Extend Display component
2. Add blur algorithms
3. Integrate with detection regions
4. Maintain performance

### Phase C: Auto Shutdown
1. Add shutdown signals
2. Graceful process termination
3. Resource cleanup
4. End-of-video detection

## 🏷️ Git Workflow

```bash
# Phase A
git checkout -b phase-a
# ... implement Phase A
git tag phase-a-v1.0
git push origin phase-a-v1.0

# Phase B  
git checkout -b phase-b
# ... implement Phase B
git tag phase-b-v1.0
git push origin phase-b-v1.0

# Phase C
git checkout -b phase-c
# ... implement Phase C
git tag phase-c-v1.0
git push origin phase-c-v1.0
```

## 🧪 Testing Strategy

- **Unit Tests**: Each component individually
- **Integration Tests**: Component communication
- **Performance Tests**: FPS and latency measurements
- **End-to-End Tests**: Complete pipeline validation

## 📈 Production-Grade Considerations

### Performance Optimization
- **Zero-copy operations** where possible with ZeroMQ
- **Asynchronous processing** to prevent blocking
- **Memory pool management** for frame buffers  
- **CPU/GPU utilization monitoring**

### Monitoring & Logging
- **Real-time metrics**: FPS, latency, memory usage, CPU load
- **Component health**: Process status, message queue depths
- **Error tracking**: Exception handling with stack traces
- **Performance profiling**: Bottleneck identification

### Production Reliability
- **Graceful error recovery**: Component restart on failure
- **Backpressure handling**: Prevent memory overflow
- **Configuration management**: Runtime parameter adjustment
- **Resource cleanup**: Proper shutdown procedures

### Scalability Design
- **Edge deployment ready**: Optimized for limited resources
- **Cloud scaling patterns**: Multi-instance coordination
- **Hardware abstraction**: Camera/display device independence
- **Network resilience**: Handle connectivity issues 

## 🎯 **Final Deliverable: Real-Time Video Pipeline Viewer**

**What we're building:**
- A **simple real-time video viewer** that demonstrates the multi-process pipeline
- Uses `cv2.imshow()` for display (no complex UI needed)
- **Focus**: Proving the 3-process architecture works smoothly
- **Goal**: Show motion detection, blurring, and timestamps in real-time

**User Experience:**
```
User runs: python main.py
→ Video window opens showing:
  - Original video with motion detection boxes
  - Timestamp in top-left corner  
  - Smooth playback (matching original FPS)
  - Blurred motion areas (Phase B)
  - Auto-closes when video ends (Phase C)
``` 