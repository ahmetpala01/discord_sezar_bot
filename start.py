#!/usr/bin/env python
"""
Bot Startup Script with FFmpeg Verification
------------------------------------------
This script verifies FFmpeg installation before starting the bot.
"""

import os
import sys
import subprocess
import shutil
import platform
import time

def verify_ffmpeg():
    """Verify FFmpeg installation and set environment variable if needed"""
    print("Verifying FFmpeg installation...")
    
    # First check environment variable
    ffmpeg_env = os.environ.get('FFMPEG_PATH')
    if ffmpeg_env and os.path.exists(ffmpeg_env):
        print(f"✅ Using FFmpeg from environment variable: {ffmpeg_env}")
        return ffmpeg_env
    
    # Check if ffmpeg is in PATH
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        print(f"✅ Found FFmpeg in system PATH: {ffmpeg_path}")
        os.environ['FFMPEG_PATH'] = ffmpeg_path
        return ffmpeg_path
    
    # Check common locations based on platform
    if platform.system() == 'Windows':
        common_locations = [
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe'
        ]
    else:
        # Linux/Mac locations
        common_locations = [
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/ffmpeg/bin/ffmpeg'
        ]
    
    # Check each location
    for location in common_locations:
        if os.path.exists(location):
            print(f"✅ Found FFmpeg at: {location}")
            os.environ['FFMPEG_PATH'] = location
            return location
    
    # If we reach this point, FFmpeg wasn't found
    print("❌ FFmpeg not found in any common location")
    
    if platform.system() == 'Windows':
        print("\nPlease install FFmpeg:")
        print("1. Download FFmpeg from https://ffmpeg.org/download.html")
        print("2. Extract to C:\\ffmpeg")
        print("3. Add C:\\ffmpeg\\bin to your PATH environment variable")
    else:
        print("\nPlease install FFmpeg:")
        print("sudo apt update && sudo apt install -y ffmpeg")
    
    # In Docker, we should never reach this point because FFmpeg is installed in the Dockerfile
    if os.path.exists('/.dockerenv'):
        print("\n⚠️ Running in Docker but FFmpeg not found!")
        print("This shouldn't happen if your Dockerfile is set up correctly.")
        print("Check your Dockerfile and ensure FFmpeg is being installed.")
    
    return None

def start_bot():
    """Start the main bot process"""
    print("\n🚀 Starting Discord bot...\n")
    
    # Use execv to replace the current process with the bot
    # This ensures proper signal handling
    os.execv(sys.executable, [sys.executable, 'main.py'])

if __name__ == "__main__":
    print(f"🤖 Initializing Sezar Discord Bot on {platform.system()}")
    print(f"Python {platform.python_version()}")
    
    # Verify FFmpeg installation
    ffmpeg_path = verify_ffmpeg()
    if not ffmpeg_path and not os.path.exists('/.dockerenv'):
        # Only exit if not in Docker and FFmpeg not found
        # In Docker, we'll try to continue since it might be at an unexpected path
        print("⚠️ FFmpeg not found but continuing anyway...")
        time.sleep(2)  # Give user time to read the warning
    
    # Start the bot
    start_bot()