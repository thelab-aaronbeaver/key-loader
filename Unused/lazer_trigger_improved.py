#!/usr/bin/env python3
"""
UDP Listener for LightBurn Trigger
Listens for UDP messages and sends Enter key to LightBurn application
"""

import socket
import subprocess
import sys
import logging
from datetime import datetime

# Configuration
UDP_IP = "0.0.0.0"  # Listen on all available interfaces
UDP_PORT = 5005
BUFFER_SIZE = 1024
TRIGGER_MESSAGE = "START"
APP_NAME = "LightBurn"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("lazer_trigger.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def send_keystroke_macos(app_name):
    """Send Enter keystroke to specified application on macOS."""
    try:
        cmd = [
            'osascript', '-e',
            f'tell application "System Events" to tell application process "{app_name}" to keystroke return'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            logger.info(f"✅ Successfully sent Enter key to {app_name}")
            return True
        else:
            logger.error(f"❌ Failed to send keystroke: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️ Timeout sending keystroke to {app_name}")
        return False
    except Exception as e:
        logger.error(f"❌ Error sending keystroke: {e}")
        return False


def main():
    """Main UDP listener loop."""
    logger.info(f"🚀 Starting LightBurn UDP Trigger Listener")
    logger.info(f"📡 Listening on {UDP_IP}:{UDP_PORT}")
    logger.info(f"🎯 Trigger message: '{TRIGGER_MESSAGE}'")
    logger.info(f"🖥️  Target application: {APP_NAME}")
    logger.info(f"Press Ctrl+C to stop\n")
    
    # Create UDP socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        logger.info(f"✅ Socket bound successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create socket: {e}")
        sys.exit(1)
    
    # Main listening loop
    try:
        while True:
            try:
                # Receive data
                data, addr = sock.recvfrom(BUFFER_SIZE)
                message = data.decode('utf-8').strip()
                
                logger.info(f"📨 Received message '{message}' from {addr[0]}:{addr[1]}")
                
                # Check if it's the trigger message
                if message == TRIGGER_MESSAGE:
                    logger.info(f"🎯 Trigger detected! Sending Enter key to {APP_NAME}...")
                    send_keystroke_macos(APP_NAME)
                else:
                    logger.warning(f"⚠️ Ignoring unknown message: '{message}'")
                    
            except UnicodeDecodeError as e:
                logger.error(f"❌ Failed to decode message: {e}")
                continue
            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
                continue
                
    except KeyboardInterrupt:
        logger.info("\n⏹️ Shutdown requested (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        sock.close()
        logger.info("🔌 Socket closed")
        logger.info("👋 Shutdown complete")


if __name__ == "__main__":
    main()

