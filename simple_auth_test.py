#!/usr/bin/env python3
"""
Simple test for OAuth2 authentication fix.
"""
import os
import sys
import json

# Set up minimal config for testing
config_data = {
    "video_dir": "d:/VIDEOS/recorder",
    "log_file": "uploaded.txt",
    "temp_dir": "temp_merged",
    "ffmpeg_path": "./ffmpeg.exe",
    "ffprobe_path": "./ffprobe.exe",
    "youtube_client_secrets": "client_secrets.json",
    "youtube_credentials": "youtube_credentials.json",
    "youtube_scopes": ["https://www.googleapis.com/auth/youtube.upload"],
    "early_morning_cutoff": 4,
    "max_file_size_gb": 2.0,
    "video_quality": "720p",
    "default_privacy": "private",
    "default_category": "20",
    "default_tags": ["gaming", "arena", "pvp"],
    "max_retries": 3,
    "retry_delay": 5
}

try:
    from config import VideoConfig
    from youtube_uploader import YouTubeUploader
    
    # Create config from dict
    config = VideoConfig(**config_data)
    
    # Create uploader
    uploader = YouTubeUploader(config)
    
    print("Starting authentication test...")
    
    # This will trigger OAuth2 flow
    uploader._build_service()
    
    print("✅ Authentication successful!")
    print("The OAuth2 fix is working correctly.")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
