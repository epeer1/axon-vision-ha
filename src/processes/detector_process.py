#!/usr/bin/env python3
"""
Motion Detector Process  
Receives frames from streamer and performs motion detection.
"""
import argparse
import signal
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.detector.motion_detector import MotionDetector


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down detector...")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Video Pipeline Motion Detector Process")
    parser.add_argument("--threshold", type=int, default=25,
                       help="Motion detection threshold (default: 25)")
    parser.add_argument("--min-area", type=int, default=500,
                       help="Minimum area for motion detection (default: 500)")
    parser.add_argument("--dilate-iterations", type=int, default=2,
                       help="Dilation iterations (default: 2)")
    parser.add_argument("--stats-interval", type=int, default=5,
                       help="Statistics display interval in seconds (default: 5)")
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("VIDEO PIPELINE - MOTION DETECTOR PROCESS")
    print("=" * 60)
    print(f"Threshold: {args.threshold}")
    print(f"Min area: {args.min_area}")
    print(f"Dilate iterations: {args.dilate_iterations}")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    # Create motion detector
    detector = MotionDetector(
        threshold=args.threshold,
        min_area=args.min_area,
        dilate_iterations=args.dilate_iterations
    )
    
    try:
        print("Starting motion detection...")
        
        # Start detection
        if not detector.start_detection():
            print("Failed to start motion detection!")
            return 1
        
        print("Motion detection started - waiting for frames from streamer...")
        
        # Monitor statistics
        last_stats_time = time.time()
        try:
            while detector.is_processing:
                time.sleep(1)
                
                # Show statistics periodically
                current_time = time.time()
                if current_time - last_stats_time >= args.stats_interval:
                    stats = detector.get_stats()
                    if stats['frames_processed'] > 0:
                        print(f"Stats: {stats['frames_processed']} frames, "
                              f"{stats['total_detections']} detections, "
                              f"avg: {stats['avg_processing_time_ms']:.1f}ms/frame")
                    last_stats_time = current_time
        
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
    
    except Exception as e:
        print(f"Detector error: {e}")
        return 1
    
    finally:
        print("Stopping motion detector...")
        detector.stop_detection()
        
        # Final statistics
        stats = detector.get_stats()
        print("-" * 60)
        print("FINAL STATISTICS:")
        print(f"Frames processed: {stats['frames_processed']}")
        print(f"Total detections: {stats['total_detections']}")
        print(f"Detections per frame: {stats['detections_per_frame']:.2f}")
        print(f"Average processing time: {stats['avg_processing_time_ms']:.1f}ms")
        print("Motion detector stopped")
    
    return 0


if __name__ == "__main__":
    exit(main()) 