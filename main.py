"""
Main video uploader application with improved architecture and error handling.
"""
import os
import logging
import time
from collections import defaultdict
from typing import List, Dict, Optional
from pathlib import Path

from config import VideoConfig, create_default_config
from exceptions import *
from video_processor import VideoProcessor, FilenameParser
from youtube_uploader import YouTubeUploader, FallbackUploader


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_uploader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class VideoUploadManager:
    """
    Main class for managing video upload operations.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the video upload manager.
        
        Args:
            config_path: Path to configuration file. If None, uses environment variables.
        """
        self.config = self._load_config(config_path)
        self.video_processor = VideoProcessor(self.config)
        self.filename_parser = FilenameParser(self.config)
        
        # Initialize uploaders
        self.youtube_uploader = YouTubeUploader(self.config)
        self.fallback_uploader = FallbackUploader(self.config)
        
        self._uploaded_files = set()
        self._load_uploaded_files()
    
    def _load_config(self, config_path: Optional[str]) -> VideoConfig:
        """Load configuration from file or environment."""
        if config_path and os.path.exists(config_path):
            config = VideoConfig.from_file(config_path)
        else:
            config = VideoConfig.from_env()
        
        # Validate configuration
        errors = config.validate()
        if errors:
            raise ConfigurationError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return config
    
    def _load_uploaded_files(self):
        """Load list of already uploaded files."""
        log_path = self.config.get_full_log_path()
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding='utf-8') as f:
                    self._uploaded_files = set(line.strip() for line in f if line.strip())
                logger.info(f"Loaded {len(self._uploaded_files)} previously uploaded files")
            except IOError as e:
                logger.warning(f"Failed to load uploaded files log: {e}")
    
    def _mark_as_uploaded(self, filenames: List[str]):
        """Mark files as uploaded in the log."""
        log_path = self.config.get_full_log_path()
        try:
            with open(log_path, "a", encoding='utf-8') as f:
                for filename in filenames:
                    f.write(f"{filename}\n")
                    self._uploaded_files.add(filename)
            logger.debug(f"Marked {len(filenames)} files as uploaded")
        except IOError as e:
            logger.error(f"Failed to update uploaded files log: {e}")
    
    def _safe_delete_file(self, file_path: str):
        """Safely delete a file with error handling."""
        if not self.config.delete_after_upload:
            logger.info(f"Skipping deletion (disabled in config): {file_path}")
            return
            
        try:
            os.remove(file_path)
            logger.info(f"Deleted: {file_path}")
        except OSError as e:
            logger.error(f"Failed to delete {file_path}: {e}")
    
    def _get_pending_videos(self) -> Dict:
        """Get videos that haven't been uploaded yet, grouped by date."""
        videos_by_date = defaultdict(list)
        
        if not os.path.exists(self.config.video_dir):
            logger.error(f"Video directory does not exist: {self.config.video_dir}")
            return videos_by_date
        
        for filename in os.listdir(self.config.video_dir):
            if not filename.endswith(".mp4") or filename in self._uploaded_files:
                continue
            
            try:
                video_date = self.filename_parser.get_video_date(filename)
                full_path = os.path.join(self.config.video_dir, filename)
                videos_by_date[video_date].append(full_path)
            except InvalidFilenameError as e:
                logger.warning(f"Skipping {filename}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing {filename}: {e}")
                continue
        
        logger.info(f"Found {sum(len(videos) for videos in videos_by_date.values())} pending videos across {len(videos_by_date)} dates")
        return videos_by_date
    
    def _upload_single_video(self, file_path: str) -> bool:
        """
        Upload a single video file.
        
        Args:
            file_path: Path to video file
            
        Returns:
            True if upload successful
        """
        filename = os.path.basename(file_path)
        
        try:
            title = self.filename_parser.parse_title(filename)
            logger.info(f"Uploading single video: {filename} with title: {title}")
            
            # Try YouTube API first, fallback to youtube-upload tool
            video_id = self.youtube_uploader.upload_video(file_path, title)
            
            if video_id:
                self._mark_as_uploaded([filename])
                logger.info(f"Successfully uploaded: {filename} (ID: {video_id})")
                self._safe_delete_file(file_path)
                return True
            else:
                # Fallback to external tool
                logger.info("Falling back to external youtube-upload tool")
                if self.fallback_uploader.upload_video(file_path, title):
                    self._mark_as_uploaded([filename])
                    logger.info(f"Successfully uploaded using fallback: {filename}")
                    self._safe_delete_file(file_path)
                    return True
                else:
                    logger.error(f"All upload methods failed for: {filename}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error uploading {filename}: {e}")
            return False
    
    def _upload_merged_video(self, video_files: List[str], date) -> bool:
        """
        Merge multiple videos and upload as single video.
        
        Args:
            video_files: List of video file paths
            date: Date for the video collection
            
        Returns:
            True if upload successful
        """
        merged_filename = f"{date.strftime('%d-%m-%Y')}_rudikiaz_arenas.mp4"
        merged_path = os.path.join(self.config.temp_dir, merged_filename)
        
        try:
            logger.info(f"Merging {len(video_files)} videos for date {date}")
            
            # Sort files by datetime for correct order
            sorted_files = sorted(
                video_files, 
                key=lambda fp: self.filename_parser.get_video_datetime(os.path.basename(fp))
            )
            
            # Merge videos
            if not self.video_processor.merge_videos(sorted_files, merged_path, overwrite=True):
                logger.error(f"Failed to merge videos for date {date}")
                return False
            
            # Create description with timestamps
            title = self.config.merged_video_title_template.format(date=date.strftime('%d-%m-%Y'))
            description = self._create_merged_description(sorted_files)
            
            logger.info(f"Uploading merged video: {merged_filename}")
            logger.debug(f"Description:\n{description}")
            
            # Try YouTube API first
            video_id = self.youtube_uploader.upload_video(
                merged_path, title, description
            )
            
            upload_success = False
            if video_id:
                logger.info(f"Successfully uploaded merged video: {merged_filename} (ID: {video_id})")
                upload_success = True
            else:
                # Fallback to external tool
                logger.info("Falling back to external youtube-upload tool for merged video")
                if self.fallback_uploader.upload_video(merged_path, title, description):
                    logger.info(f"Successfully uploaded merged video using fallback: {merged_filename}")
                    upload_success = True
            
            if upload_success:
                # Mark individual files as uploaded
                filenames = [os.path.basename(fp) for fp in video_files]
                self._mark_as_uploaded(filenames)
                
                # Clean up files
                self._safe_delete_file(merged_path)
                for file_path in video_files:
                    self._safe_delete_file(file_path)
                
                return True
            else:
                logger.error(f"All upload methods failed for merged video: {merged_filename}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing merged video for date {date}: {e}")
            return False
    
    def _create_merged_description(self, sorted_files: List[str]) -> str:
        """Create description with timestamps for merged video."""
        description_lines = []
        offset = 0.0
        
        for file_path in sorted_files:
            try:
                formatted_offset = self.video_processor.format_time(offset)
                clip_desc = self.filename_parser.extract_clip_description(
                    os.path.basename(file_path)
                )
                description_lines.append(f"{formatted_offset}  {clip_desc}")
                
                duration = self.video_processor.get_video_duration(file_path)
                offset += duration
            except Exception as e:
                logger.warning(f"Error processing clip description for {file_path}: {e}")
                continue
        
        return "\n".join(description_lines)
    
    def process_videos(self) -> Dict[str, int]:
        """
        Process all pending videos.
        
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'total_processed': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'single_videos': 0,
            'merged_videos': 0
        }
        
        try:
            # Ensure temp directory exists
            os.makedirs(self.config.temp_dir, exist_ok=True)
            
            videos_by_date = self._get_pending_videos()
            
            if not videos_by_date:
                logger.info("No pending videos to process")
                return stats
            
            for date, video_files in videos_by_date.items():
                stats['total_processed'] += len(video_files)
                
                if len(video_files) == 1:
                    # Single video upload
                    if self._upload_single_video(video_files[0]):
                        stats['successful_uploads'] += 1
                        stats['single_videos'] += 1
                    else:
                        stats['failed_uploads'] += 1
                else:
                    # Multiple videos - merge and upload
                    if self._upload_merged_video(video_files, date):
                        stats['successful_uploads'] += len(video_files)
                        stats['merged_videos'] += 1
                    else:
                        stats['failed_uploads'] += len(video_files)
                
                # Add delay between uploads to avoid rate limiting
                time.sleep(2)
            
            logger.info(f"Processing complete. Stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Unexpected error during video processing: {e}")
            raise


def main():
    """Main entry point."""
    try:
        # Create default config if it doesn't exist
        config_file = "config.json"
        if not os.path.exists(config_file):
            logger.info("Creating default configuration file")
            create_default_config(config_file)
            logger.info(f"Please edit {config_file} with your settings and run again")
            return
        
        # Initialize and run uploader
        uploader = VideoUploadManager(config_file)
        stats = uploader.process_videos()
        
        logger.info("Video upload process completed successfully")
        logger.info(f"Final statistics: {stats}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
