#!/usr/bin/env python3
"""
Test script to debug imports in the executable.
"""
import sys
import os

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    import main
    print('✅ main import works')
except Exception as e:
    print(f'❌ main import error: {e}')

try:
    import youtube_uploader
    print('✅ youtube_uploader import works')
except Exception as e:
    print(f'❌ youtube_uploader import error: {e}')

try:
    import config
    print('✅ config import works')
except Exception as e:
    print(f'❌ config import error: {e}')

try:
    import exceptions
    print('✅ exceptions import works')
except Exception as e:
    print(f'❌ exceptions import error: {e}')

try:
    import video_processor
    print('✅ video_processor import works')
except Exception as e:
    print(f'❌ video_processor import error: {e}')
