#!/usr/bin/env python3
"""
Phase A Runner - Complete Video Processing Pipeline Demonstration
Orchestrates all pipeline components: Logging → Streamer → Detector → Display
"""
import argparse
import subprocess
import sys
import time
import signal
import os
from pathlib import Path
from typing import List, Optional


class PipelineOrchestrator:
    """Manages the complete video processing pipeline."""
    
    def __init__(self, video_path: str, blur_detections: bool = False):
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
            print("VIDEO PROCESSING PIPELINE - PHASE A DEMONSTRATION")
            print("=" * 80)
            print(f"Video file: {self.video_path}")
            print(f"Motion blur: {'Enabled' if self.blur_detections else 'Disabled'}")
            print(f"Python executable: {sys.executable}")
            print("-" * 80)
            
            # Validate video file
            if not self.video_path.exists():
                print(f"ERROR: Video file not found: {self.video_path}")
                return False
            
            print("Starting pipeline components...")
            
            # 1. Start Centralized Logging Service
            print("  [1/4] Starting centralized logging service...")
            logging_cmd = [sys.executable, "src/processes/logging_service.py", "--verbose"]
            logging_process = subprocess.Popen(logging_cmd, 
                                             stdout=subprocess.PIPE, 
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)
            self.processes.append(logging_process)
            time.sleep(2)  # Give logging service time to start
            
            # 2. Start Motion Detector Process FIRST (it binds the socket for display)
            print("  [2/5] Starting motion detector process...")
            detector_cmd = [sys.executable, "src/processes/detector_process.py", "--stats-interval", "10"]
            detector_process = subprocess.Popen(detector_cmd,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.STDOUT,
                                              universal_newlines=True)
            self.processes.append(detector_process)
            time.sleep(3)  # Give detector time to bind sockets
            
            # 3. Start Web Streamer Process (binds web server)
            print("  [3/5] Starting web streamer process...")
            web_streamer_cmd = [sys.executable, "src/processes/web_streamer_process.py", "--port", "5000"]
            web_streamer_process = subprocess.Popen(web_streamer_cmd,
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.STDOUT,
                                                   universal_newlines=True)
            self.processes.append(web_streamer_process)
            time.sleep(3)  # Give web streamer time to start
            
            # 4. Start Video Display Process (connects to detector, binds for web)
            print("  [4/5] Starting video display process...")
            display_cmd = [sys.executable, "src/processes/display_process.py", "--no-window"]
            display_process = subprocess.Popen(display_cmd,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)
            self.processes.append(display_process)
            time.sleep(2)  # Give display time to connect
            
            # 5. Start Video Streamer Process (LAST - starts the data flow)
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
            print("PIPELINE ARCHITECTURE:")
            print("  Streamer Process  → (ZMQ) → Detector Process")
            print("  Detector Process  → (ZMQ) → Display Process")
            print("  Display Process   → (ZMQ) → Web Streamer Process")
            print("  Web Streamer      → (HTTP) → Browser Display")
            print("  All Components    → (ZMQ) → Logging Service")
            print("-" * 80)
            print("WEB STREAMING INTERFACE:")
            print("  URL: http://127.0.0.1:5000")
            print("  Opening browser automatically in 5 seconds...")
            print("-" * 80)
            print("WHAT YOU SHOULD SEE:")
            print("  1. Real-time video stream with motion detection boxes")
            print("  2. Live statistics (FPS, frames processed, uptime)")
            print("  3. Professional web interface with controls")
            print("  4. Centralized logging in 'pipeline.log' file")
            print("-" * 80)
            print("CONTROLS:")
            print("  Browser    = View live video stream")
            print("  Ctrl+C     = Stop entire pipeline")
            print("-" * 80)
            
            # Auto-open browser after a short delay
            import threading
            import webbrowser
            def open_browser():
                import time
                time.sleep(5)  # Give web server time to start
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
        """Monitor pipeline processes and handle completion."""
        try:
            print("Pipeline monitoring started...")
            print("Monitoring process status...")
            
            while not self.shutdown_requested:
                time.sleep(2)
                
                # Check if any process has terminated
                terminated_processes = []
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:  # Process has terminated
                        terminated_processes.append((i, process))
                
                if terminated_processes:
                    process_names = ["Logging", "Detector", "WebStreamer", "Display", "Streamer"]
                    for i, process in terminated_processes:
                        process_name = process_names[i] if i < len(process_names) else f"Process{i}"
                        exit_code = process.returncode
                        print(f"  {process_name} process terminated (exit code: {exit_code})")
                    
                    # If streamer (video source) terminates, pipeline is done
                    if any(i == 4 for i, _ in terminated_processes):  # Streamer is index 4
                        print("\nVideo streaming completed - pipeline finished!")
                        break
                    
                    # If display terminates, user probably closed window
                    if any(i == 3 for i, _ in terminated_processes):  # Display is index 3
                        print("\nDisplay window closed - stopping pipeline")
                        break
            
        except KeyboardInterrupt:
            print("\nPipeline monitoring interrupted by user")
        
        finally:
            print("\nShutting down pipeline...")
            self.stop_pipeline()
    
    def stop_pipeline(self):
        """Stop all pipeline processes gracefully."""
        if not self.processes:
            return
        
        print("Stopping pipeline components...")
        
        # Stop processes in reverse order (streamer first to stop data flow)
        process_names = ["Logging", "Detector", "WebStreamer", "Display", "Streamer"]
        for i in reversed(range(len(self.processes))):
            if i < len(self.processes):
                process = self.processes[i]
                name = process_names[i] if i < len(process_names) else f"Process{i}"
                
                if process.poll() is None:  # Process still running
                    print(f"  Stopping {name} process...")
                    try:
                        process.terminate()
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        print(f"    Force killing {name} process...")
                        process.kill()
                        process.wait()
                    except Exception as e:
                        print(f"    Error stopping {name}: {e}")
        
        self.processes.clear()
        print("Pipeline shutdown complete")
    
    def show_logs(self):
        """Display the centralized log file if it exists."""
        log_file = Path("pipeline.log")
        if log_file.exists():
            print("-" * 80)
            print("CENTRALIZED PIPELINE LOG:")
            print("-" * 80)
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    print(f.read())
            except Exception as e:
                print(f"Error reading log file: {e}")
        else:
            print("No log file found")


def main():
    parser = argparse.ArgumentParser(
        description="Phase A Runner - Complete Video Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python phase_a_runner.py "People - 6387.mp4"
  python phase_a_runner.py "People - 6387.mp4" --blur-detections
  python phase_a_runner.py "People - 6387.mp4" --show-logs
        """
    )
    
    parser.add_argument("video_file", help="Path to video file")
    parser.add_argument("--blur-detections", action="store_true",
                       help="Enable motion blur on detected areas (Phase B feature)")
    parser.add_argument("--show-logs", action="store_true",
                       help="Show centralized log file after pipeline stops")
    
    args = parser.parse_args()
    
    # Create and run pipeline
    orchestrator = PipelineOrchestrator(args.video_file, args.blur_detections)
    
    try:
        # Start pipeline
        if not orchestrator.start_pipeline():
            return 1
        
        # Monitor until completion
        orchestrator.monitor_pipeline()
        
        # Optionally show logs
        if args.show_logs:
            orchestrator.show_logs()
        
        print("\nPhase A pipeline demonstration completed successfully!")
        print("Check 'pipeline.log' for detailed execution logs")
        
        return 0
        
    except Exception as e:
        print(f"Pipeline error: {e}")
        orchestrator.stop_pipeline()
        return 1


if __name__ == "__main__":
    exit(main()) 