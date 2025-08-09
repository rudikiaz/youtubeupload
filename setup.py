"""
Setup and installation script for the Enhanced Video Uploader.
"""
import os
import sys
import subprocess
import json
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def install_requirements():
    """Install required Python packages."""
    print("📦 Installing Python packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False


def check_ffmpeg():
    """Check if FFmpeg is available."""
    print("🔍 Checking FFmpeg...")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFmpeg is available")
            return True
        else:
            print("❌ FFmpeg check failed")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ FFmpeg not found")
        print("Please install FFmpeg from: https://ffmpeg.org/download.html")
        return False


def create_config():
    """Create default configuration file."""
    config_file = "config.json"
    
    if os.path.exists(config_file):
        print(f"✅ Configuration file already exists: {config_file}")
        return True
    
    print(f"🔧 Creating default configuration: {config_file}")
    
    # Get user input for key settings
    video_dir = input("Enter video directory path [d:/VIDEOS/recorder]: ").strip()
    if not video_dir:
        video_dir = "d:/VIDEOS/recorder"
    
    config = {
        "video_dir": video_dir,
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
        "merged_video_title_template": "Rudikiaz arenas for {date}",
        "individual_video_title_template": "{username} {activity}",
        "max_retries": 3,
        "retry_delay": 5,
        "delete_after_upload": True
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Created {config_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to create config file: {e}")
        return False


def check_youtube_credentials():
    """Check for YouTube API credentials."""
    print("🔍 Checking YouTube API credentials...")
    
    if os.path.exists("client_secrets.json"):
        print("✅ client_secrets.json found")
        return True
    else:
        print("❌ client_secrets.json not found")
        print("\n� YOUTUBE API CREDENTIALS SETUP REQUIRED")
        print("="*60)
        print("Follow these detailed steps to set up YouTube API access:")
        print()
        print("1. 🌐 Go to Google Cloud Console:")
        print("   https://console.cloud.google.com/")
        print()
        print("2. 📁 Create or select a project:")
        print("   - Click 'Select a project' dropdown at the top")
        print("   - Create a new project or select an existing one")
        print()
        print("3. 🔌 Enable YouTube Data API v3:")
        print("   - Go to 'APIs & Services' > 'Library'")
        print("   - Search for 'YouTube Data API v3'")
        print("   - Click on it and press 'Enable'")
        print()
        print("4. 🔐 Create OAuth 2.0 credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click '+ CREATE CREDENTIALS' > 'OAuth client ID'")
        print("   - Choose 'Desktop application' as application type")
        print("   - Give it a name (e.g., 'YouTube Video Uploader')")
        print("   - Click 'Create'")
        print()
        print("5. 💾 Download the credentials:")
        print("   - In the credentials list, find your new OAuth 2.0 client")
        print("   - Click the download button (⬇️) on the right")
        print("   - Rename the downloaded file to 'client_secrets.json'")
        print("   - Place it in this directory")
        print()
        print("📚 More info: https://developers.google.com/youtube/v3/getting-started")
        print("="*60)
        return False


def create_run_script():
    """Create a simple run script."""
    script_content = '''#!/usr/bin/env python3
"""
Simple run script for the Enhanced Video Uploader.
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import main
    main()
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
'''
    
    with open("run.py", "w") as f:
        f.write(script_content)
    
    # Make executable on Unix systems
    if os.name != 'nt':
        os.chmod("run.py", 0o755)
    
    print("✅ Created run.py script")


def main():
    """Main setup function."""
    print("🚀 Enhanced Video Uploader Setup")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed: Could not install requirements")
        return False
    
    # Check FFmpeg
    ffmpeg_ok = check_ffmpeg()
    
    # Create configuration
    config_ok = create_config()
    
    # Check YouTube credentials
    youtube_ok = check_youtube_credentials()
    
    # Create run script
    create_run_script()
    
    print("\n" + "=" * 40)
    print("📋 Setup Summary:")
    print(f"✅ Python version: OK")
    print(f"{'✅' if True else '❌'} Requirements: {'OK' if True else 'FAILED'}")
    print(f"{'✅' if ffmpeg_ok else '❌'} FFmpeg: {'OK' if ffmpeg_ok else 'MISSING'}")
    print(f"{'✅' if config_ok else '❌'} Configuration: {'OK' if config_ok else 'FAILED'}")
    print(f"{'✅' if youtube_ok else '❌'} YouTube API: {'OK' if youtube_ok else 'MISSING'}")
    
    if all([config_ok, youtube_ok, ffmpeg_ok]):
        print("\n🎉 Setup completed successfully!")
        print("Run: python run.py")
    else:
        print("\n⚠️  Setup completed with warnings. Please fix the issues above.")
    
    return True


if __name__ == "__main__":
    main()
