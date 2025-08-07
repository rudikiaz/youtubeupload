"""
Package initialization file for video uploader.
"""

from .config import VideoConfig, create_default_config
from .exceptions import *
from .video_processor import VideoProcessor, FilenameParser
from .youtube_uploader import YouTubeUploader, FallbackUploader
from .main import VideoUploadManager

__version__ = "2.0.0"
__author__ = "rudikiaz"

__all__ = [
    'VideoConfig',
    'create_default_config', 
    'VideoProcessor',
    'FilenameParser',
    'YouTubeUploader',
    'FallbackUploader',
    'VideoUploadManager',
    # Exceptions
    'VideoUploaderError',
    'ConfigurationError',
    'VideoProcessingError',
    'FFmpegError',
    'YouTubeUploadError',
    'AuthenticationError',
    'FileOperationError',
    'InvalidFilenameError'
]
