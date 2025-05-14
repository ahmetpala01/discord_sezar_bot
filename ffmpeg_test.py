#!/usr/bin/env python
"""
FFmpeg Test Script
-----------------
This script verifies FFmpeg installation and availability.
Run locally to check your development environment.
Run in Docker to check your production environment.
"""

import os
import subprocess
import shutil
import platform
import sys

def test_ffmpeg():
    """Test if FFmpeg is properly installed and accessible"""
    print(f"Testing FFmpeg on {platform.system()} ({platform.release()})")
    
    # Method 1: Check environment variable
    ffmpeg_env = os.environ.get('FFMPEG_PATH')
    if ffmpeg_env and os.path.exists(ffmpeg_env):
        print(f"✅ FFmpeg found in environment variable: {ffmpeg_env}")
        executable = ffmpeg_env
    else:
        print("❌ FFMPEG_PATH environment variable not set or invalid")
        
        # Method 2: Check in system PATH
        executable = shutil.which('ffmpeg')
        if executable:
            print(f"✅ FFmpeg found in system PATH: {executable}")
        else:
            print("❌ FFmpeg not found in system PATH")
            
            # Method 3: Check common locations
            common_locations = []
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
                
            for location in common_locations:
                if os.path.exists(location):
                    print(f"✅ FFmpeg found in common location: {location}")
                    executable = location
                    break
            else:
                print("❌ FFmpeg not found in any common location")
    
    # If FFmpeg was found, test it
    if executable:
        try:
            # Run FFmpeg version command
            result = subprocess.run(
                [executable, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print("\n✅ FFmpeg is working correctly!")
                print(f"Version information:\n{result.stdout.splitlines()[0]}")
                return True
            else:
                print("\n❌ FFmpeg returned an error:")
                print(result.stderr)
                return False
        except Exception as e:
            print(f"\n❌ Error running FFmpeg: {str(e)}")
            return False
    else:
        print("\n❌ FFmpeg executable not found")
        print("Please install FFmpeg and make sure it's in your PATH or set FFMPEG_PATH")
        return False

if __name__ == "__main__":
    success = test_ffmpeg()
    if not success:
        if platform.system() == 'Windows':
            print("\n📝 Installation instructions for Windows:")
            print("1. Download FFmpeg from https://ffmpeg.org/download.html")
            print("2. Extract to C:\\ffmpeg")
            print("3. Add C:\\ffmpeg\\bin to your PATH environment variable")
        else:
            print("\n📝 Installation instructions for Linux:")
            print("In Docker (already in your Dockerfile):")
            print("  RUN apt-get update && apt-get install -y ffmpeg")
            print("On host system:")
            print("  sudo apt update && sudo apt install -y ffmpeg")
        
        sys.exit(1)
    sys.exit(0)