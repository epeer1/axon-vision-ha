#!/usr/bin/env python3
"""
Runner script for the video processing pipeline with phase selection.
"""
import sys
import subprocess
from pathlib import Path
import argparse


def main():
    """Run the video processing pipeline for a specific phase."""
    parser = argparse.ArgumentParser(
        description="Video Processing Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Phases:
  a - Basic pipeline with motion detection
  b - Pipeline with motion blur on detected areas
  c - Pipeline with automatic shutdown on video end

Examples:
  python run_pipeline.py                           # Run phase A with default video
  python run_pipeline.py -p b                      # Run phase B with default video
  python run_pipeline.py -p c "video.mp4"          # Run phase C with custom video
  python run_pipeline.py "video.mp4" -p b          # Run phase B with custom video
  python run_pipeline.py -p b --no-blur            # Run phase B without blur
        """
    )
    
    parser.add_argument("video_file", nargs="?", default="data/People - 6387.mp4",
                       help="Path to video file (default: data/People - 6387.mp4)")
    parser.add_argument("-p", "--phase", choices=["a", "b", "c"], default="a",
                       help="Pipeline phase to run (default: a)")
    parser.add_argument("--no-blur", action="store_true",
                       help="Disable motion blur (phase B/C only)")
    parser.add_argument("--blur-detections", action="store_true",
                       help="Enable motion blur (phase A only)")
    parser.add_argument("--show-logs", action="store_true",
                       help="Show centralized log file after pipeline stops")
    
    args, extra_args = parser.parse_known_args()
    
    # Check if video file exists
    if not Path(args.video_file).exists():
        print(f"Error: Video file not found: {args.video_file}")
        return 1
    
    # Determine which phase runner to use
    phase_runners = {
        "a": "src/phase_a_runner.py",
        "b": "src/phase_b_runner.py", 
        "c": "src/phase_c_runner.py"
    }
    
    runner = phase_runners[args.phase]
    
    # Build command
    cmd = [sys.executable, runner, args.video_file]
    
    # Add phase-specific arguments
    if args.phase == "a":
        if args.blur_detections:
            cmd.append("--blur-detections")
    elif args.phase in ["b", "c"]:
        if args.no_blur:
            cmd.append("--no-blur")
    
    if args.show_logs:
        cmd.append("--show-logs")
    
    # Add any extra arguments
    cmd.extend(extra_args)
    
    # Display what we're running
    print("=" * 60)
    print(f"RUNNING PHASE {args.phase.upper()} PIPELINE")
    print("=" * 60)
    print(f"Video: {args.video_file}")
    print(f"Phase: {args.phase.upper()} - ", end="")
    
    if args.phase == "a":
        print("Basic motion detection pipeline")
        if args.blur_detections:
            print("  + Motion blur enabled")
    elif args.phase == "b":
        print("Pipeline with motion blur")
        if args.no_blur:
            print("  + Motion blur disabled (for comparison)")
    elif args.phase == "c":
        print("Pipeline with automatic shutdown")
        if not args.no_blur:
            print("  + Motion blur enabled")
    
    print("-" * 60)
    
    # Run the pipeline
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        return 0
    except FileNotFoundError:
        print(f"Error: Phase runner not found: {runner}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 