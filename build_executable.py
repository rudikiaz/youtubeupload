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


def create_embedded_uploader():
    """Create a modified youtube_uploader.py file with embedded client secrets."""
    print("🔐 Embedding client secrets directly into youtube_uploader.py...")
    
    # Read client secrets
    client_secrets_path = 'client_secrets.json'
    if not os.path.exists(client_secrets_path):
        print(f"❌ Client secrets file not found: {client_secrets_path}")
        return False
    
    import json
    with open(client_secrets_path, 'r') as f:
        client_secrets = json.load(f)
    
    # Read the original youtube_uploader.py
    with open('youtube_uploader.py', 'r', encoding='utf-8') as f:
        original_code = f.read()
    
    # Create backup
    with open('youtube_uploader_backup.py', 'w', encoding='utf-8') as f:
        f.write(original_code)
    
    # Embed client secrets at the top of the file
    embedded_secrets_code = f'''
# Embedded client secrets for executable
EMBEDDED_CLIENT_SECRETS = {json.dumps(client_secrets, indent=4)}

import tempfile
import json
'''
    
    # Insert embedded secrets after the imports section
    import_section_end = original_code.find('logger = logging.getLogger(__name__)')
    if import_section_end == -1:
        print("❌ Could not find logger definition in youtube_uploader.py")
        return False
    
    # Insert the embedded code before the logger line
    modified_code = (
        original_code[:import_section_end] + 
        embedded_secrets_code + 
        original_code[import_section_end:]
    )
    
    # Replace the _get_credentials method to use embedded secrets
    old_get_credentials = '''    def _get_credentials(self) -> Credentials:
        """
        Get valid credentials for YouTube API.
        
        Returns:
            Valid Google OAuth2 credentials
            
        Raises:
            AuthenticationError: If authentication fails
        """
        creds = None
        
        # Load existing credentials
        if os.path.exists(self.config.youtube_credentials):
            try:
                creds = Credentials.from_authorized_user_file(
                    self.config.youtube_credentials, self.config.youtube_scopes
                )
                logger.debug("Loaded existing credentials")
            except Exception as e:
                logger.warning(f"Failed to load existing credentials: {e}")
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed expired credentials")
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.config.youtube_client_secrets):
                    self._print_setup_instructions()
                    raise AuthenticationError(
                        f"Client secrets file not found: {self.config.youtube_client_secrets}. "
                        f"Please follow the setup instructions above to obtain this file."
                    )
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.config.youtube_client_secrets, self.config.youtube_scopes
                    )'''
    
    new_get_credentials = '''    def _get_credentials(self) -> Credentials:
        """
        Get valid credentials for YouTube API.
        
        Returns:
            Valid Google OAuth2 credentials
            
        Raises:
            AuthenticationError: If authentication fails
        """
        creds = None
        
        # Load existing credentials
        if os.path.exists(self.config.youtube_credentials):
            try:
                creds = Credentials.from_authorized_user_file(
                    self.config.youtube_credentials, self.config.youtube_scopes
                )
                logger.debug("Loaded existing credentials")
            except Exception as e:
                logger.warning(f"Failed to load existing credentials: {e}")
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed expired credentials")
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                # Use embedded client secrets
                temp_secrets_file = None
                try:
                    # Create temporary file with embedded secrets
                    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                    json.dump(EMBEDDED_CLIENT_SECRETS, temp_file, indent=2)
                    temp_file.close()
                    temp_secrets_file = temp_file.name
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        temp_secrets_file, self.config.youtube_scopes
                    )'''
    
    modified_code = modified_code.replace(old_get_credentials, new_get_credentials)
    
    # Also add cleanup for temp file at the end of the method
    old_method_end = '''                except Exception as e:
                    raise AuthenticationError(f"Failed to obtain new credentials: {e}")
        
        # Save credentials
        try:
            with open(self.config.youtube_credentials, 'w') as token:
                token.write(creds.to_json())
            logger.debug("Saved credentials to file")
        except Exception as e:
            logger.warning(f"Failed to save credentials: {e}")
        
        return creds'''
    
    new_method_end = '''                except Exception as e:
                    raise AuthenticationError(f"Failed to obtain new credentials: {e}")
                finally:
                    # Clean up temporary secrets file
                    if temp_secrets_file:
                        try:
                            os.unlink(temp_secrets_file)
                        except:
                            pass
        
        # Save credentials
        try:
            with open(self.config.youtube_credentials, 'w') as token:
                token.write(creds.to_json())
            logger.debug("Saved credentials to file")
        except Exception as e:
            logger.warning(f"Failed to save credentials: {e}")
        
        return creds'''
    
    modified_code = modified_code.replace(old_method_end, new_method_end)
    
    # Enable web OAuth by default - modify the authentication logic
    old_auth_logic = '''                    # Check if manual flow is forced or if we're in a headless environment
                    force_manual = os.getenv('FORCE_MANUAL_OAUTH', '').lower() in ('true', '1', 'yes')
                    
                    # Detect headless environment
                    is_headless = (
                        os.getenv('DISPLAY') is None and os.name != 'nt'  # Linux/Mac without display
                        or os.getenv('SSH_CLIENT') is not None  # SSH session
                        or os.getenv('SSH_TTY') is not None
                        or force_manual
                    )
                    
                    if not is_headless:
                        # Try to run local server first
                        try:
                            creds = flow.run_local_server(port=0)
                            logger.info("Obtained new credentials via local server")
                        except Exception as browser_error:
                            logger.warning(f"Local server auth failed: {browser_error}")
                            logger.info("Falling back to manual authorization flow")
                            
                            # Fallback to manual flow for headless environments
                            creds = self._manual_oauth_flow(flow)
                            logger.info("Obtained new credentials via manual flow")
                    else:
                        # Use manual flow for headless environments
                        logger.info("Headless environment detected, using manual OAuth flow")
                        creds = self._manual_oauth_flow(flow)
                        logger.info("Obtained new credentials via manual flow")'''
    
    new_auth_logic = '''                    # Force web OAuth by default (disable manual mode unless explicitly requested)
                    force_manual = os.getenv('FORCE_MANUAL_OAUTH', '').lower() in ('true', '1', 'yes')
                    
                    if not force_manual:
                        # Use web OAuth by default
                        try:
                            print("🌐 Starting web OAuth authentication...")
                            print("📝 A browser window will open for YouTube authorization")
                            print("💡 If the browser doesn't open automatically, copy the URL from the terminal")
                            creds = flow.run_local_server(port=0)
                            logger.info("Obtained new credentials via web OAuth")
                        except Exception as browser_error:
                            logger.warning(f"Web OAuth failed: {browser_error}")
                            logger.info("Falling back to manual authorization flow")
                            
                            # Fallback to manual flow
                            creds = self._manual_oauth_flow(flow)
                            logger.info("Obtained new credentials via manual flow")
                    else:
                        # Use manual flow when explicitly requested
                        logger.info("Manual OAuth flow requested")
                        creds = self._manual_oauth_flow(flow)
                        logger.info("Obtained new credentials via manual flow")'''
    
    modified_code = modified_code.replace(old_auth_logic, new_auth_logic)
    
    # Write the modified version
    with open('youtube_uploader.py', 'w', encoding='utf-8') as f:
        f.write(modified_code)
    
    print("✅ Successfully embedded client secrets into youtube_uploader.py")
    return True


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
        'main',
        'config',
        'exceptions',
        'video_processor',
        'youtube_uploader',
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
    print("✅ Copied executable with embedded client secrets")
    
    # Create example config file (without sensitive data)
    example_config = {
        "video_dir": "C:/Videos/recorder",
        "log_file": "uploaded.txt",
        "temp_dir": "temp_merged",
        "ffmpeg_path": "./ffmpeg.exe",
        "ffprobe_path": "./ffprobe.exe",
        "youtube_client_secrets": "client_secrets.json",  # Not used, but kept for compatibility
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
    readme_content = """# YouTube Video Uploader - Executable Distribution (Embedded Secrets)

## Quick Start

1. **Setup Configuration:**
   - Copy config.json.example to config.json
   - Edit config.json with your settings:
     - Set video_dir to your video folder path
     - Adjust other settings as needed

2. **Setup FFmpeg:**
   - Download FFmpeg from: https://ffmpeg.org/download.html
   - Place ffmpeg.exe and ffprobe.exe in this directory
   - Or install FFmpeg system-wide and update paths in config.json

3. **Run the uploader:**
   youtube_uploader.exe

## Authentication

✅ **Client secrets are embedded** - No need for client_secrets.json!
🌐 **Web OAuth by default** - A browser will open for authentication

On first run:
- The application will open your web browser automatically
- Log in with your Google/YouTube account
- Grant permissions to the application
- The browser will show a success message
- Return to the terminal to continue

### Manual OAuth (if needed)
If automatic browser opening fails, set environment variable:
```
set FORCE_MANUAL_OAUTH=true
youtube_uploader.exe
```

## File Structure
distribution/
├── youtube_uploader.exe     # Main executable (with embedded secrets)
├── config.json.example     # Configuration template
├── config.json            # Your configuration (create this)
├── ffmpeg.exe             # Video processing (you provide)
├── ffprobe.exe            # Video analysis (you provide)
├── youtube_credentials.json # Auto-generated after first auth
├── uploaded.txt           # Upload log (auto-generated)
└── temp_merged/           # Temporary files (auto-generated)

## Notes

- Client secrets are embedded in the executable - no external secrets file needed
- Web OAuth authentication is enabled by default for better user experience
- First run will prompt for YouTube authentication via browser
- Config file must be in the same directory as the executable
- Log files and temporary directories are created automatically

## Troubleshooting

- Ensure all paths in config.json are correct
- Check that FFmpeg executables are accessible
- If browser doesn't open, manually copy the URL shown in terminal
- For headless environments, use FORCE_MANUAL_OAUTH=true
- Check the log files for detailed error information

## Environment Variables

- `FORCE_MANUAL_OAUTH=true` - Force manual OAuth flow instead of web browser
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
    print("2. Add ffmpeg.exe and ffprobe.exe")
    print("3. Run youtube_uploader.exe or run_uploader.bat")
    print("\n🔐 Client secrets are embedded - no additional API setup needed!")
    print("🌐 Web OAuth authentication will start automatically on first run")
    
    return True


def main():
    """Main build process."""
    print("🚀 YouTube Video Uploader - Build Script (with embedded secrets)")
    print("=" * 60)
    
    # Check dependencies
    if not check_pyinstaller():
        sys.exit(1)
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create embedded uploader with hardcoded client secrets
    if not create_embedded_uploader():
        sys.exit(1)
    
    try:
        # Create build specification
        create_build_spec()
        
        # Build executable
        if not build_executable():
            print("❌ Build failed - restoring original files")
            sys.exit(1)
        
        # Create distribution package
        if not create_distribution_package():
            print("❌ Distribution package creation failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Build process failed: {e}")
        sys.exit(1)
    finally:
        # Restore original uploader if backup exists
        if os.path.exists('youtube_uploader_backup.py'):
            if os.path.exists('youtube_uploader.py'):
                os.remove('youtube_uploader.py')
            shutil.move('youtube_uploader_backup.py', 'youtube_uploader.py')
            print("🔄 Restored original youtube_uploader.py")
    
    print("\n✅ Build completed successfully!")
    print("📦 Check the 'distribution' folder for your executable package")
    print("🔐 Client secrets are now embedded in the executable")
    print("🌐 Web OAuth authentication is enabled by default")


if __name__ == "__main__":
    main()