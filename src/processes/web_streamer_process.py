#!/usr/bin/env python3
"""
Web Streamer Process - HTTP streaming server for real-time video pipeline.
"""
import argparse
import signal
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.display.web_streamer import WebStreamer


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down web streamer...")
    sys.exit(0)


def main():
    """Main web streamer process."""
    parser = argparse.ArgumentParser(description='Video Pipeline Web Streamer')
    parser.add_argument('--port', type=int, default=5000, help='HTTP server port (default: 5000)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Server host (default: 127.0.0.1)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and configure web streamer
    try:
        print("=" * 60)
        print("VIDEO PIPELINE - WEB STREAMER PROCESS")
        print("=" * 60)
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"URL: http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        # Create web streamer
        streamer = WebStreamer(port=args.port, host=args.host)
        
        print("Starting web streaming server...")
        print(f"Open http://{args.host}:{args.port} in your browser")
        print("Waiting for processed frames from pipeline...")
        print()
        
        # Start streaming (blocking)
        success = streamer.start_streaming()
        
        if not success:
            print("Failed to start web streaming")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Web streamer error: {e}")
        sys.exit(1)
    finally:
        try:
            streamer.stop_streaming()
        except:
            pass
        print("Web streamer stopped")


if __name__ == "__main__":
    main() 