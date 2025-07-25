#!/usr/bin/env python3
"""
Centralized Logging Service Process
Collects and manages logs from all pipeline components.
"""
import argparse
import signal
import sys
import time

from utils.centralized_logger import CentralizedLogger


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down logging service...")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Video Pipeline Centralized Logging Service")
    parser.add_argument("--log-file", default="pipeline.log", 
                       help="Log file path (default: pipeline.log)")
    parser.add_argument("--no-console", action="store_true",
                       help="Disable console output (file only)")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("VIDEO PIPELINE - CENTRALIZED LOGGING SERVICE")
    print("=" * 60)
    print(f"Log file: {args.log_file}")
    print(f"Console output: {not args.no_console}")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    # Create and start logging service
    logger = CentralizedLogger(
        log_file=args.log_file,
        console_output=not args.no_console
    )
    
    try:
        if not logger.start_logging():
            print("Failed to start logging service!")
            return 1
        
        print("Centralized logging service started successfully")
        print("Waiting for log messages from pipeline components...")
        
        # Keep service running
        try:
            while True:
                time.sleep(1)
                
                # Show statistics periodically
                if args.verbose:
                    stats = logger.get_stats()
                    if stats['messages_logged'] > 0:
                        print(f"\rMessages logged: {stats['messages_logged']}", end="", flush=True)
        
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
    
    except Exception as e:
        print(f"Logging service error: {e}")
        return 1
    
    finally:
        print("Stopping logging service...")
        logger.stop_logging()
        print("Logging service stopped")
    
    return 0


if __name__ == "__main__":
    exit(main()) 