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
├── README.md
├── assignment-description.md
├── ARCHITECTURE.md
├── requirements.txt
├── 
├── # Phase Runners (Demo Each Development Stage)
├── phase_a_runner.py         # Basic pipeline demo
├── phase_b_runner.py         # Pipeline + motion blur demo
├── phase_c_runner.py         # Full system + auto-shutdown demo
├── 
├── # Process Services (Separate Processes)
├── streamer_process.py       # Video streaming service
├── detector_process.py       # Motion detection service  
├── display_process.py        # Display/rendering service
├── 
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── communication.py
├── core/
│   ├── __init__.py
│   ├── base_component.py
│   └── data_models.py
├── components/
│   ├── __init__.py
│   ├── streamer/
│   │   ├── __init__.py
│   │   ├── video_streamer.py
│   │   └── frame_reader.py
│   ├── detector/
│   │   ├── __init__.py
│   │   ├── motion_detector.py
│   │   └── opencv_detector.py
│   └── display/
│       ├── __init__.py
│       ├── video_display.py
│       └── frame_renderer.py
├── communication/
│   ├── __init__.py
│   ├── zmq_manager.py
│   ├── message_handler.py
│   └── protocol.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   ├── performance_monitor.py
│   └── config_loader.py
├── tests/
│   ├── __init__.py
│   ├── test_streamer.py
│   ├── test_detector.py
│   └── test_display.py
├── assets/
│   └── People - 6387.mp4
└── docs/
    ├── phase_a.md
    ├── phase_b.md
    └── phase_c.md
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

### ⭐ **CHOSEN: ZeroMQ Sockets (Production-Grade)**
- **Pros**: High performance, optimized for video, non-blocking, industry standard
- **Cons**: External dependency (pip install pyzmq)
- **Use Case**: Production real-time video processing systems
- **Why**: Perfect for Axon's production infrastructure requirements

### Alternative Options:
- **Multiprocessing Queues**: Simple but serialization overhead for video frames
- **Shared Memory**: Fastest but complex synchronization
- **Named Pipes**: OS-specific, complex for cross-platform deployment

**Decision Rationale**: ZeroMQ is the industry standard for high-performance video processing pipelines, demonstrating production-ready architecture skills.

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