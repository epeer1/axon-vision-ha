# Software Assignment - Video Processing Pipeline System Implementation

## Phase A - Building a Distributed Pipeline System

### General Description
Build a video analytics system consisting of three main components, where each component runs in a separate process. The components communicate with each other to create a Pipeline architecture:

### System Components:

#### 1. Streamer
- **Input**: Video file path/address
- **Operation**: Extract frame by frame from the video
- **Output**: Send each frame to the Detector component

#### 2. Detector
- **Input**: Single frame from the Streamer
- **Operation**:
  - Perform Motion Detection on the frame
  - You may use the OpenCV Detector implementation (provided in separate file)
  - **DO NOT draw on the image!**
- **Output**: Send the frame as-is + detection information to the Display component

#### 3. Display
- **Input**: Frame and detection information
- **Operation**:
  - Draw the detections on the image
  - Write current timestamp in the top-left corner of the image
  - Display the video on screen smoothly

## Phase B - Blurring on Detections

- Extend the "Display" component to perform **Blurring** on detected areas
- You can use any blurring algorithm (e.g., Gaussian Blur, Median Blur)
- **Goal**: Blur the areas where motion was detected

## Phase C - System Shutdown and Cleanup

- Add new feature: **Automatic shutdown of all processes** when video ends
- When the video finishes:
  - All components (processes) should close in an orderly manner

## Important Guidelines

- **Free choice in inter-component communication** – explain your choice (Sockets, Queues, Pipes, etc.)
- **Drawing on image should only be done in the "Display" component**
- Work according to phase order and preserve code from each phase without destroying previous code
  - Recommended to use Git and tag each phase separately
- **No need to improve detection quality** – use the OpenCV Detector algorithm as provided
- **Main focus in Phase A**: Build a stable, well-timed system with smooth video display (no stuttering or frame skipping)
- Test video is provided

## Technical Requirements

### Architecture
- Multi-process system (not multi-threading)
- Pipeline architecture with clear separation of concerns
- Each component runs independently and communicates via chosen IPC method

### Performance
- Smooth video playback without frame drops
- Real-time processing capabilities
- Proper synchronization between components

### Code Organization
- Clean, maintainable code structure
- Version control with Git tags for each phase
- Clear documentation of communication method choice

## Deliverables

1. **Phase A**: Working pipeline with Streamer → Detector → Display
2. **Phase B**: Enhanced Display component with motion blur functionality
3. **Phase C**: Complete system with automatic shutdown capability
4. **Documentation**: Explanation of chosen communication method and architecture decisions
5. **Version Control**: Git repository with proper tagging for each phase 