#!/usr/bin/env python3
"""
Build script for creating executable distribution of YouTube Video Uploader.

This script creates a standalone executable that includes only the Python code.
External dependencies (ffmpeg, config files, credentials) are kept separate.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print("✅ PyInstaller is available")
        return True
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=5.10.0"])
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyInstaller")
            return False


def clean_build_dirs():
    """Clean previous build directories."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}/")
            shutil.rmtree(dir_name)
    
    # Clean .spec files
    for spec_file in Path('.').glob('*.spec'):
        print(f"🧹 Removing {spec_file}")
        spec_file.unlink()


def create_build_spec():
    """Create PyInstaller spec file for custom build configuration."""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# List of Python modules to include
a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'google.auth',
        'google.oauth2',
        'google_auth_oauthlib',
        'googleapiclient',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='youtube_uploader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""
    
    with open('youtube_uploader.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Created PyInstaller spec file")


def build_executable():
    """Build the executable using PyInstaller."""
    print("🔨 Building executable...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "youtube_uploader.spec"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Executable built successfully!")
            return True
        else:
            print("❌ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False


def create_distribution_package():
    """Create a distribution package with the executable and required files."""
    if not os.path.exists('dist/youtube_uploader.exe'):
        print("❌ Executable not found!")
        return False
    
    # Create distribution directory
    dist_dir = Path('distribution')
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    dist_dir.mkdir()
    
    # Copy executable
    shutil.copy2('dist/youtube_uploader.exe', dist_dir / 'youtube_uploader.exe')
    print("✅ Copied executable")
    
    # Create example config file (without sensitive data)
    example_config = {
        "video_dir": "C:/Videos/recorder",
        "log_file": "uploaded.txt",
        "temp_dir": "temp_merged",
        "ffmpeg_path": "./ffmpeg.exe",
        "ffprobe_path": "./ffprobe.exe",
        "youtube_client_secrets": "client_secrets.json",
        "youtube_credentials": "youtube_credentials.json",
        "youtube_scopes": ["https://www.googleapis.com/auth/youtube.upload"],
        "early_morning_cutoff": 4,
        "max_file_size_gb": 2.0,
        "video_quality": "1440p",
        "default_privacy": "private",
        "default_category": "20",
        "default_tags": ["gaming", "arena", "pvp"],
        "merged_video_title_template": "Rudikiaz arenas for {date}",
        "individual_video_title_template": "{username} {activity}",
        "max_retries": 3,
        "retry_delay": 5,
        "delete_after_upload": True
    }
    
    import json
    with open(dist_dir / 'config.json.example', 'w') as f:
        json.dump(example_config, f, indent=2)
    
    print("✅ Created example config file")
    
    # Create README for distribution
    readme_content = """# YouTube Video Uploader - Executable Distribution

## Quick Start

1. **Setup Configuration:**
   - Copy config.json.example to config.json
   - Edit config.json with your settings:
     - Set video_dir to your video folder path
     - Adjust other settings as needed

2. **Setup YouTube API:**
   - Place your client_secrets.json file in this directory
   - Get it from: https://console.developers.google.com/

3. **Setup FFmpeg:**
   - Download FFmpeg from: https://ffmpeg.org/download.html
   - Place ffmpeg.exe and ffprobe.exe in this directory
   - Or install FFmpeg system-wide and update paths in config.json

4. **Run the uploader:**
   youtube_uploader.exe

## File Structure
distribution/
├── youtube_uploader.exe     # Main executable
├── config.json.example     # Configuration template
├── config.json            # Your configuration (create this)
├── client_secrets.json    # YouTube API credentials (you provide)
├── ffmpeg.exe             # Video processing (you provide)
├── ffprobe.exe            # Video analysis (you provide)
├── youtube_credentials.json # Auto-generated after first auth
├── uploaded.txt           # Upload log (auto-generated)
└── temp_merged/           # Temporary files (auto-generated)

## Notes

- The executable contains only the Python application code
- External dependencies (FFmpeg, config, credentials) are separate files
- First run will prompt for YouTube authentication
- Config file must be in the same directory as the executable
- Log files and temporary directories are created automatically

## Troubleshooting

- Ensure all paths in config.json are correct
- Check that FFmpeg executables are accessible
- Verify YouTube API credentials are valid
- Check the log files for detailed error information
"""
    
    with open(dist_dir / 'README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ Created distribution README")
    
    # Create batch file for easy execution
    batch_content = """@echo off
echo Starting YouTube Video Uploader...
echo.
youtube_uploader.exe
echo.
echo Upload process completed.
pause
"""
    
    with open(dist_dir / 'run_uploader.bat', 'w') as f:
        f.write(batch_content)
    
    print("✅ Created run batch file")
    
    print(f"\n🎉 Distribution package created in: {dist_dir.absolute()}")
    print("\nTo complete the setup:")
    print("1. Copy config.json.example to config.json and edit it")
    print("2. Add your client_secrets.json file")
    print("3. Add ffmpeg.exe and ffprobe.exe")
    print("4. Run youtube_uploader.exe or run_uploader.bat")
    
    return True


def main():
    """Main build process."""
    print("🚀 YouTube Video Uploader - Build Script")
    print("=" * 50)
    
    # Check dependencies
    if not check_pyinstaller():
        sys.exit(1)
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create build specification
    create_build_spec()
    
    # Build executable
    if not build_executable():
        sys.exit(1)
    
    # Create distribution package
    if not create_distribution_package():
        sys.exit(1)
    
    print("\n✅ Build completed successfully!")
    print("📦 Check the 'distribution' folder for your executable package")


if __name__ == "__main__":
    main()