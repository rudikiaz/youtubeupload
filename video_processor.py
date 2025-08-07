"""
Video processing utilities for merging and manipulating video files.
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

from config import VideoConfig
from exceptions import FFmpegError, VideoProcessingError, InvalidFilenameError


logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video processing operations like merging and format conversion."""
    
    def __init__(self, config: VideoConfig):
        self.config = config
        self._ensure_temp_dir()
    
    def _ensure_temp_dir(self) -> None:
        """Ensure temporary directory exists."""
        temp_path = self.config.get_full_temp_path()
        os.makedirs(temp_path, exist_ok=True)
    
    def get_video_duration(self, file_path: str) -> float:
        """
        Get video duration in seconds using ffprobe.
        
        Args:
            file_path: Path to video file
            
        Returns:
            Duration in seconds
            
        Raises:
            FFmpegError: If ffprobe fails
        """
        cmd = [
            self.config.ffprobe_path,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            logger.debug(f"Duration for {file_path}: {duration}s")
            return duration
        except subprocess.CalledProcessError as e:
            raise FFmpegError(f"Failed to get duration for {file_path}: {e.stderr}")
        except ValueError as e:
            raise FFmpegError(f"Invalid duration output for {file_path}: {result.stdout}")
    
    def get_video_info(self, file_path: str) -> dict:
        """
        Get comprehensive video information using ffprobe.
        
        Args:
            file_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        cmd = [
            self.config.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise FFmpegError(f"Failed to get video info for {file_path}: {e.stderr}")
        except json.JSONDecodeError as e:
            raise FFmpegError(f"Invalid JSON output from ffprobe: {e}")
    
    def format_time(self, seconds: float) -> str:
        """
        Format seconds as MM:SS or HH:MM:SS.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        seconds = int(round(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def merge_videos(self, file_list: List[str], output_file: str, 
                    overwrite: bool = False) -> bool:
        """
        Merge multiple videos into a single file using FFmpeg.
        
        Args:
            file_list: List of video file paths to merge
            output_file: Output file path
            overwrite: Whether to overwrite existing output file
            
        Returns:
            True if merge successful, False otherwise
            
        Raises:
            FFmpegError: If merge fails
            VideoProcessingError: If input validation fails
        """
        if not file_list:
            raise VideoProcessingError("No files provided for merging")
        
        if os.path.exists(output_file) and not overwrite:
            logger.info(f"Output file already exists: {output_file}")
            return True
        
        # Validate input files
        for file_path in file_list:
            if not os.path.exists(file_path):
                raise VideoProcessingError(f"Input file does not exist: {file_path}")
        
        # Create file list for FFmpeg
        temp_path = self.config.get_full_temp_path()
        list_file = os.path.join(temp_path, "file_list.txt")
        try:
            with open(list_file, "w", encoding='utf-8') as f:
                for file_path in file_list:
                    # Properly escape path for FFmpeg
                    escaped_path = file_path.replace("\\", "/").replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
        except IOError as e:
            raise VideoProcessingError(f"Failed to create file list: {e}")
        
        # FFmpeg command
        cmd = [
            self.config.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy"
        ]
        
        if overwrite:
            cmd.append("-y")
        
        cmd.append(output_file)
        
        logger.info(f"Merging {len(file_list)} videos to {output_file}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Successfully merged videos to {output_file}")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg merge failed: {e.stderr}"
            logger.error(error_msg)
            raise FFmpegError(error_msg)
        finally:
            # Clean up temporary file list
            try:
                os.remove(list_file)
            except OSError:
                pass
    
    def compress_video(self, input_file: str, output_file: str, 
                      target_size_mb: Optional[float] = None) -> bool:
        """
        Compress video to reduce file size.
        
        Args:
            input_file: Input video file path
            output_file: Output video file path
            target_size_mb: Target file size in MB
            
        Returns:
            True if compression successful
        """
        cmd = [
            self.config.ffmpeg_path,
            "-i", input_file,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23"
        ]
        
        if target_size_mb:
            # Calculate bitrate for target file size
            duration = self.get_video_duration(input_file)
            target_bitrate = int((target_size_mb * 8 * 1024) / duration)  # kbps
            cmd.extend(["-b:v", f"{target_bitrate}k"])
        
        cmd.extend(["-c:a", "aac", "-b:a", "128k", "-y", output_file])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Successfully compressed video: {output_file}")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Video compression failed: {e.stderr}"
            logger.error(error_msg)
            raise FFmpegError(error_msg)


class FilenameParser:
    """Handles parsing and validation of video filenames."""
    
    def __init__(self, config: VideoConfig):
        self.config = config
    
    def parse_title(self, filename: str) -> str:
        """
        Extract title from filename.
        
        Args:
            filename: Video filename
            
        Returns:
            Formatted title string
            
        Raises:
            InvalidFilenameError: If filename format is invalid
        """
        try:
            parts = filename.split(" - ")
            if len(parts) < 3:
                raise InvalidFilenameError(f"Invalid filename format: {filename}")
            
            username = parts[1]
            activity_part = parts[2].split(" (")[0]
            activity_words = activity_part.split()
            
            if len(activity_words) < 2:
                raise InvalidFilenameError(f"Not enough words in activity part: {filename}")
            
            first_two_words = " ".join(activity_words[:2]).lower()
            return f"{username} {first_two_words}"
            
        except Exception as e:
            raise InvalidFilenameError(f"Error parsing title from {filename}: {e}")
    
    def get_video_datetime(self, filename: str) -> datetime:
        """
        Parse datetime from filename with early morning adjustment.
        
        Args:
            filename: Video filename
            
        Returns:
            Parsed datetime
            
        Raises:
            InvalidFilenameError: If datetime parsing fails
        """
        try:
            parts = filename.split(" - ")
            full_timestamp = parts[0]
            dt = datetime.strptime(full_timestamp, "%Y-%m-%d %H-%M-%S")
            
            # Adjust for early morning videos
            if dt.hour < self.config.early_morning_cutoff:
                dt -= timedelta(days=1)
                
            return dt
        except Exception as e:
            raise InvalidFilenameError(f"Invalid datetime format in filename {filename}: {e}")
    
    def get_video_date(self, filename: str):
        """Get the date component from filename."""
        return self.get_video_datetime(filename).date()
    
    def extract_clip_description(self, filename: str) -> str:
        """
        Extract clip description from filename.
        
        Args:
            filename: Video filename
            
        Returns:
            Clip description without timestamp and extension
        """
        if filename.endswith(".mp4"):
            filename = filename[:-4]
        
        parts = filename.split(" - ")
        if len(parts) > 1:
            return " - ".join(parts[1:])
        return filename
