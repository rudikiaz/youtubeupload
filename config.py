"""
Configuration module for video uploader.
Handles all configuration parameters and environment variables.
"""
import os
import logging
import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import json


logger = logging.getLogger(__name__)


@dataclass
class VideoConfig:
    """Configuration class for video processing and upload settings."""
    
    # Directory settings
    video_dir: str
    log_file: str
    temp_dir: str
    
    # FFmpeg settings
    ffmpeg_path: str
    ffprobe_path: str
    
    # YouTube upload settings
    youtube_client_secrets: str
    youtube_credentials: str
    youtube_scopes: list
    
    # Video processing settings
    early_morning_cutoff: int = 4  # Videos before 4 AM count as previous day
    max_file_size_gb: float = 2.0  # Maximum file size for upload
    video_quality: str = "720p"
    
    # Upload settings
    default_privacy: str = "private"  # private, public, unlisted
    default_category: str = "20"  # Gaming category
    default_tags: list = None
    
    # Error handling
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    
    def __post_init__(self):
        if self.default_tags is None:
            self.default_tags = ["gaming", "arena", "pvp"]
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        # Create temp directory if it doesn't exist
        if not os.path.isabs(self.temp_dir):
            # Relative path - create in current working directory
            temp_path = os.path.join(os.getcwd(), self.temp_dir)
        else:
            temp_path = self.temp_dir
        
        os.makedirs(temp_path, exist_ok=True)
        logger.debug(f"Ensured temp directory exists: {temp_path}")
        
        # Create video directory if it doesn't exist (and it's absolute)
        if os.path.isabs(self.video_dir):
            os.makedirs(self.video_dir, exist_ok=True)
            logger.debug(f"Ensured video directory exists: {self.video_dir}")
    
    def get_full_log_path(self) -> str:
        """Get the full path for the log file."""
        if os.path.isabs(self.log_file):
            return self.log_file
        return os.path.join(os.getcwd(), self.log_file)
    
    def get_full_temp_path(self) -> str:
        """Get the full path for the temp directory."""
        if os.path.isabs(self.temp_dir):
            return self.temp_dir
        return os.path.join(os.getcwd(), self.temp_dir)
    
    @classmethod
    def from_file(cls, config_path: str) -> 'VideoConfig':
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        return cls(**config_data)
    
    @classmethod
    def from_env(cls) -> 'VideoConfig':
        """Load configuration from environment variables with defaults."""
        return cls(
            video_dir=os.getenv('VIDEO_DIR', 'd:/VIDEOS/recorder'),
            log_file=os.getenv('LOG_FILE', 'uploaded.txt'),
            temp_dir=os.getenv('TEMP_DIR', 'temp_merged'),
            ffmpeg_path=os.getenv('FFMPEG_PATH', './ffmpeg.exe'),
            ffprobe_path=os.getenv('FFPROBE_PATH', './ffprobe.exe'),
            youtube_client_secrets=os.getenv('YOUTUBE_CLIENT_SECRETS', 'client_secrets.json'),
            youtube_credentials=os.getenv('YOUTUBE_CREDENTIALS', 'youtube_credentials.json'),
            youtube_scopes=os.getenv('YOUTUBE_SCOPES', 'https://www.googleapis.com/auth/youtube.upload').split(','),
            early_morning_cutoff=int(os.getenv('EARLY_MORNING_CUTOFF', '4')),
            max_file_size_gb=float(os.getenv('MAX_FILE_SIZE_GB', '2.0')),
            video_quality=os.getenv('VIDEO_QUALITY', '720p'),
            default_privacy=os.getenv('DEFAULT_PRIVACY', 'private'),
            default_category=os.getenv('DEFAULT_CATEGORY', '20'),
            default_tags=os.getenv('DEFAULT_TAGS', 'gaming,arena,pvp').split(','),
            max_retries=int(os.getenv('MAX_RETRIES', '3')),
            retry_delay=int(os.getenv('RETRY_DELAY', '5'))
        )
    
    def validate(self) -> list:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not os.path.exists(self.video_dir):
            errors.append(f"Video directory does not exist: {self.video_dir}")
        
        # Check if ffmpeg/ffprobe are available
        try:
            import subprocess
            subprocess.run([self.ffmpeg_path, '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            errors.append(f"FFmpeg not found at: {self.ffmpeg_path}")
        
        try:
            subprocess.run([self.ffprobe_path, '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            errors.append(f"FFprobe not found at: {self.ffprobe_path}")
        
        return errors


def create_default_config(config_path: str) -> None:
    """Create a default configuration file."""
    default_config = {
        "video_dir": "/mnt/d/VIDEOS/recorder",
        "log_file": "/mnt/d/VIDEOS/recorder/uploaded.txt",
        "temp_dir": "/mnt/d/VIDEOS/recorder/temp_merged",
        "ffmpeg_path": "ffmpeg",
        "ffprobe_path": "ffprobe",
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
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
