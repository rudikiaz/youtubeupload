"""
Custom exceptions for the video uploader.
"""


class VideoUploaderError(Exception):
    """Base exception for video uploader errors."""
    pass


class ConfigurationError(VideoUploaderError):
    """Raised when configuration is invalid."""
    pass


class VideoProcessingError(VideoUploaderError):
    """Raised when video processing fails."""
    pass


class FFmpegError(VideoProcessingError):
    """Raised when FFmpeg operations fail."""
    pass


class YouTubeUploadError(VideoUploaderError):
    """Raised when YouTube upload fails."""
    pass


class AuthenticationError(YouTubeUploadError):
    """Raised when YouTube authentication fails."""
    pass


class FileOperationError(VideoUploaderError):
    """Raised when file operations fail."""
    pass


class InvalidFilenameError(VideoUploaderError):
    """Raised when filename doesn't match expected format."""
    pass
