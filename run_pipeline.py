#!/usr/bin/env python3
"""
Simple runner script for the video processing pipeline.
"""
import sys
import subprocess
from pathlib import Path

def main():
    """Run the video processing pipeline."""
    # Default video file
    video_file = "data/People - 6387.mp4"
    
    # Check if a video file was provided
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
    
    # Check if video file exists
    if not Path(video_file).exists():
        print(f"Error: Video file not found: {video_file}")
        print(f"Usage: python run_pipeline.py [video_file]")
        print(f"Default: {video_file}")
        return 1
    
    # Run the phase A runner
    cmd = [sys.executable, "src/phase_a_runner.py", video_file]
    
    # Add any additional arguments
    if len(sys.argv) > 2:
        cmd.extend(sys.argv[2:])
    
    # Run the pipeline
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 