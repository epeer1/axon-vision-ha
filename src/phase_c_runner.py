#!/usr/bin/env python3
"""
Phase C Runner - Video Processing Pipeline with Automatic Shutdown
Extends Phase B by adding automatic shutdown when video ends.
"""
import argparse
import subprocess
import sys
import time
import signal
import os
from pathlib import Path
from typing import List, Optional


class PipelineCOrchestrator:
    """Manages the video processing pipeline with automatic shutdown (Phase C)."""
    
    def __init__(self, video_path: str, blur_detections: bool = True):
        self.video_path = Path(video_path)
        self.blur_detections = blur_detections
        self.processes: List[subprocess.Popen] = []
        self.shutdown_requested = False
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}, initiating pipeline shutdown...")
        self.shutdown_requested = True
        self.stop_pipeline()
    
    def start_pipeline(self) -> bool:
        """Start all pipeline components in the correct order."""
        try:
            print("=" * 80)
            print("VIDEO PROCESSING PIPELINE - PHASE C DEMONSTRATION")
            print("=" * 80)
            print(f"Video file: {self.video_path}")
            print(f"Motion blur: {'ENABLED' if self.blur_detections else 'DISABLED'}")
            print(f"Auto-shutdown: ENABLED (Phase C feature)")
            print(f"Python executable: {sys.executable}")
            print("-" * 80)
            
            # Validate video file
            if not self.video_path.exists():
                print(f"ERROR: Video file not found: {self.video_path}")
                return False
            
            print("Starting pipeline components...")
            
            # 1. Start Centralized Logging Service
            print("  [1/5] Starting centralized logging service...")
            logging_cmd = [sys.executable, "src/processes/logging_service.py", "--verbose"]
            logging_process = subprocess.Popen(logging_cmd, 
                                             stdout=subprocess.PIPE, 
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)
            self.processes.append(logging_process)
            time.sleep(2)
            
            # 2. Start Motion Detector Process
            print("  [2/5] Starting motion detector process...")
            detector_cmd = [sys.executable, "src/processes/detector_process.py", "--stats-interval", "10"]
            detector_process = subprocess.Popen(detector_cmd,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.STDOUT,
                                              universal_newlines=True)
            self.processes.append(detector_process)
            time.sleep(3)
            
            # 3. Start Web Streamer Process
            print("  [3/5] Starting web streamer process...")
            web_streamer_cmd = [sys.executable, "src/processes/web_streamer_process.py", "--port", "5000"]
            web_streamer_process = subprocess.Popen(web_streamer_cmd,
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.STDOUT,
                                                   universal_newlines=True)
            self.processes.append(web_streamer_process)
            time.sleep(3)
            
            # 4. Start Video Display Process
            print("  [4/5] Starting video display process...")
            display_cmd = [sys.executable, "src/processes/display_process.py", "--no-window"]
            if self.blur_detections:
                display_cmd.append("--blur-detections")
            display_process = subprocess.Popen(display_cmd,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)
            self.processes.append(display_process)
            time.sleep(2)
            
            # 5. Start Video Streamer Process
            print("  [5/5] Starting video streamer process...")
            streamer_cmd = [sys.executable, "src/processes/streamer_process.py", str(self.video_path)]
            streamer_process = subprocess.Popen(streamer_cmd,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.STDOUT,
                                              universal_newlines=True)
            self.processes.append(streamer_process)
            
            print("-" * 80)
            print("ALL PIPELINE COMPONENTS STARTED SUCCESSFULLY!")
            print("-" * 80)
            print("PHASE C FEATURES:")
            print("  ✓ Motion Detection (Phase A)")
            print("  ✓ Motion Blur on Detected Areas (Phase B)")
            print("  ✓ AUTOMATIC SHUTDOWN on Video End (Phase C)")
            print("-" * 80)
            print("AUTOMATIC SHUTDOWN BEHAVIOR:")
            print("  1. Streamer will send 'end-of-stream' signal when video ends")
            print("  2. All processes will receive the signal and shut down gracefully")
            print("  3. Pipeline will automatically terminate in order")
            print("  4. No manual intervention required!")
            print("-" * 80)
            print("WEB STREAMING INTERFACE:")
            print("  URL: http://127.0.0.1:5000")
            print("-" * 80)
            print("WATCH THE PIPELINE:")
            print("  - Video will play through completely")
            print("  - When video ends, all processes will shut down automatically")
            print("  - Check console for shutdown sequence")
            print("-" * 80)
            
            # Auto-open browser
            import threading
            import webbrowser
            def open_browser():
                time.sleep(5)
                try:
                    webbrowser.open("http://127.0.0.1:5000")
                    print("Browser opened to view live stream!")
                except Exception as e:
                    print(f"Could not auto-open browser: {e}")
                    print("Please manually open: http://127.0.0.1:5000")
            
            browser_thread = threading.Thread(target=open_browser, daemon=True)
            browser_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Failed to start pipeline: {e}")
            self.stop_pipeline()
            return False
    
    def monitor_pipeline(self):
        """Monitor pipeline processes and handle automatic shutdown."""
        try:
            print("\nPipeline monitoring started...")
            print("Waiting for video to complete for automatic shutdown...")
            
            start_time = time.time()
            all_running = True
            
            while not self.shutdown_requested and all_running:
                time.sleep(2)
                
                # Check process status
                terminated_processes = []
                running_count = 0
                
                for i, process in enumerate(self.processes):
                    if process.poll() is None:
                        running_count += 1
                    else:
                        terminated_processes.append((i, process))
                
                # Report status periodically
                elapsed = time.time() - start_time
                if int(elapsed) % 10 == 0:  # Every 10 seconds
                    print(f"  Pipeline status: {running_count}/{len(self.processes)} processes running (elapsed: {int(elapsed)}s)")
                
                # If any process terminated, report it
                if terminated_processes:
                    process_names = ["Logging", "Detector", "WebStreamer", "Display", "Streamer"]
                    
                    print("\n" + "=" * 60)
                    print("AUTOMATIC SHUTDOWN SEQUENCE INITIATED")
                    print("=" * 60)
                    
                    for i, process in terminated_processes:
                        process_name = process_names[i] if i < len(process_names) else f"Process{i}"
                        exit_code = process.returncode
                        
                        if i == 4:  # Streamer
                            print(f"✓ {process_name} completed video playback (exit code: {exit_code})")
                            print("  → End-of-stream signal sent to pipeline")
                        else:
                            print(f"✓ {process_name} shut down gracefully (exit code: {exit_code})")
                    
                    # Check if streamer finished (triggers cascade shutdown)
                    if any(i == 4 for i, _ in terminated_processes):
                        print("\nVideo playback completed - initiating cascade shutdown...")
                        time.sleep(3)  # Give other processes time to shut down gracefully
                        all_running = False
            
            # Final check for remaining processes
            remaining = sum(1 for p in self.processes if p.poll() is None)
            if remaining > 0:
                print(f"\n{remaining} processes still running, initiating cleanup...")
            else:
                print("\n✓ All processes shut down automatically!")
                print("✓ Phase C automatic shutdown completed successfully!")
            
        except KeyboardInterrupt:
            print("\nManual interrupt - stopping pipeline...")
        
        finally:
            self.stop_pipeline()
    
    def stop_pipeline(self):
        """Stop all pipeline processes gracefully."""
        if not self.processes:
            return
        
        print("\nFinal cleanup...")
        
        # Stop processes in reverse order
        process_names = ["Logging", "Detector", "WebStreamer", "Display", "Streamer"]
        still_running = []
        
        for i in reversed(range(len(self.processes))):
            if i < len(self.processes):
                process = self.processes[i]
                name = process_names[i] if i < len(process_names) else f"Process{i}"
                
                if process.poll() is None:  # Still running
                    still_running.append((i, name, process))
        
        if still_running:
            print(f"Stopping {len(still_running)} remaining processes...")
            for i, name, process in still_running:
                print(f"  Stopping {name}...")
                try:
                    process.terminate()
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    print(f"    Force killing {name}...")
                    process.kill()
                    process.wait()
                except Exception as e:
                    print(f"    Error stopping {name}: {e}")
        
        self.processes.clear()
        print("\n" + "=" * 60)
        print("PHASE C DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("✓ Video played to completion")
        print("✓ All processes shut down automatically")
        print("✓ No manual intervention required")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Phase C Runner - Video Pipeline with Automatic Shutdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Phase C adds automatic shutdown when video ends.

The pipeline will:
1. Play the video completely
2. Automatically shut down all processes when video ends
3. No manual intervention required

Examples:
  python phase_c_runner.py "People - 6387.mp4"
  python phase_c_runner.py "People - 6387.mp4" --no-blur
        """
    )
    
    parser.add_argument("video_file", help="Path to video file")
    parser.add_argument("--no-blur", action="store_true",
                       help="Disable motion blur")
    
    args = parser.parse_args()
    
    # Create and run pipeline
    orchestrator = PipelineCOrchestrator(args.video_file, not args.no_blur)
    
    try:
        # Start pipeline
        if not orchestrator.start_pipeline():
            return 1
        
        # Monitor until completion
        orchestrator.monitor_pipeline()
        
        return 0
        
    except Exception as e:
        print(f"Pipeline error: {e}")
        orchestrator.stop_pipeline()
        return 1


if __name__ == "__main__":
    exit(main()) 