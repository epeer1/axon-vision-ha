#!/usr/bin/env python3
"""
Video Streamer Process
Reads video file and streams frames to the detection pipeline.
"""
import argparse
import signal
import sys
import time
from pathlib import Path

from components.streamer.video_streamer import VideoStreamer


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down streamer...")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Video Pipeline Streamer Process")
    parser.add_argument("video_file", help="Path to video file")
    parser.add_argument("--fps", type=float, default=None,
                       help="Target FPS (default: use original video FPS)")
    parser.add_argument("--loop", action="store_true",
                       help="Loop video continuously")
    
    args = parser.parse_args()
    
    # Validate video file
    video_path = Path(args.video_file)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        return 1
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("VIDEO PIPELINE - STREAMER PROCESS")
    print("=" * 60)
    print(f"Video file: {video_path}")
    print(f"Target FPS: {args.fps or 'Original'}")
    print(f"Loop mode: {args.loop}")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    # Create streamer
    streamer = VideoStreamer(str(video_path), target_fps=args.fps)
    
    try:
        loop_count = 0
        while True:
            loop_count += 1
            if args.loop:
                print(f"Starting playback (loop {loop_count})...")
            else:
                print("Starting video streaming...")
            
            # Start streaming
            if not streamer.start_streaming():
                print("Failed to start streaming!")
                return 1
            
            print("Streaming started - sending frames to detector...")
            
            # Monitor progress
            try:
                while streamer.is_streaming:
                    time.sleep(1)
                    progress = streamer.get_progress()
                    print(f"\rProgress: {progress['progress']:.1f}% "
                          f"({progress['frame_id']}/{progress['total_frames']}) "
                          f"FPS: {progress['fps']:.1f}", 
                          end="", flush=True)
            
            except KeyboardInterrupt:
                print("\nShutdown requested by user")
                break
            
            print(f"\nVideo streaming completed (loop {loop_count})")
            
            if not args.loop:
                break
            
            print("Waiting 2 seconds before next loop...")
            time.sleep(2)
    
    except Exception as e:
        print(f"Streamer error: {e}")
        return 1
    
    finally:
        print("Stopping streamer...")
        streamer.stop_streaming()
        print("Streamer stopped")
    
    return 0


if __name__ == "__main__":
    exit(main()) 