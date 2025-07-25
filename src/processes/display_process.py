#!/usr/bin/env python3
"""
Video Display Process
Displays video with motion detection overlays using OpenCV.
"""
import argparse
import signal
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.display.video_display import VideoDisplay


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down display...")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Video Pipeline Display Process")
    parser.add_argument("--window-name", default="Motion Detection Pipeline",
                       help="OpenCV window name (default: Motion Detection Pipeline)")
    parser.add_argument("--no-fps", action="store_true",
                       help="Disable FPS counter display")
    parser.add_argument("--blur-detections", action="store_true",
                       help="Enable motion blur on detected areas (Phase B)")
    parser.add_argument("--no-window", action="store_true",
                       help="Disable cv2.imshow window (forward to web only)")
    parser.add_argument("--stats-interval", type=int, default=10,
                       help="Statistics display interval in seconds (default: 10)")
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("VIDEO PIPELINE - DISPLAY PROCESS")
    print("=" * 60)
    print(f"Window name: {args.window_name}")
    print(f"Show FPS: {not args.no_fps}")
    print(f"Motion blur: {args.blur_detections}")
    print("Controls: ESC=quit, P=pause/resume")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    # Create video display
    display = VideoDisplay(
        window_name=args.window_name,
        show_fps=not args.no_fps,
        blur_detections=args.blur_detections,
        show_window=not args.no_window
    )
    
    try:
        if args.no_window:
            print("Starting video display (forwarding mode - no window)...")
            print("Processing and forwarding frames to web streamer")
        else:
            print("Starting video display...")
            print("Display window should appear shortly...")
        
        # Start display
        if not display.start_display():
            print("Failed to start video display!")
            return 1
        
        print("Video display started - waiting for frames from detector...")
        
        # Monitor statistics
        last_stats_time = time.time()
        try:
            while display.is_displaying:
                time.sleep(1)
                
                # Show statistics periodically
                current_time = time.time()
                if current_time - last_stats_time >= args.stats_interval:
                    stats = display.get_stats()
                    if stats['frames_displayed'] > 0:
                        print(f"Stats: {stats['frames_displayed']} frames displayed, "
                              f"{stats['detections_drawn']} detections drawn, "
                              f"avg FPS: {stats['average_fps']:.1f}")
                    last_stats_time = current_time
        
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
    
    except Exception as e:
        print(f"Display error: {e}")
        return 1
    
    finally:
        print("Stopping video display...")
        display.stop_display()
        
        # Final statistics
        stats = display.get_stats()
        print("-" * 60)
        print("FINAL STATISTICS:")
        print(f"Frames displayed: {stats['frames_displayed']}")
        print(f"Detections drawn: {stats['detections_drawn']}")
        print(f"Average FPS: {stats['average_fps']:.1f}")
        print(f"Session duration: {stats['elapsed_time']:.1f}s")
        print("Video display stopped")
    
    return 0


if __name__ == "__main__":
    exit(main()) 