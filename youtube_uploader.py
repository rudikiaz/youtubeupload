"""
Enhanced YouTube uploader with improved OAuth2 handling and error recovery.
"""
import os
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Google API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

from config import VideoConfig
from exceptions import YouTubeUploadError, AuthenticationError


logger = logging.getLogger(__name__)


class YouTubeUploader:
    """
    Enhanced YouTube uploader with OAuth2 credential management and retry logic.
    """
    
    def __init__(self, config: VideoConfig):
        self.config = config
        self.service = None
        self._credentials = None
        
        if not GOOGLE_APIS_AVAILABLE:
            logger.warning("Google API libraries not available. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    
    def _print_setup_instructions(self):
        """Print detailed instructions for setting up YouTube API credentials."""
        print("\n" + "="*80)
        print("❌ YOUTUBE API CREDENTIALS SETUP REQUIRED")
        print("="*80)
        print("📋 To set up YouTube API credentials:")
        print("")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Enable the YouTube Data API v3:")
        print("   • Go to APIs & Services > Library")
        print("   • Search for 'YouTube Data API v3'")
        print("   • Click on it and enable it")
        print("4. Create OAuth 2.0 credentials:")
        print("   • Go to APIs & Services > Credentials")
        print("   • Click 'Create Credentials' > 'OAuth 2.0 Client ID'")
        print("   • Choose 'Desktop application' as the application type")
        print("   • Give it a name (e.g., 'YouTube Video Uploader')")
        print("   • Download the credentials JSON file")
        print("5. Rename the downloaded file to 'client_secrets.json'")
        print("6. Place it in the same directory as this application")
        print("")
        print("🔗 Direct link: https://console.cloud.google.com/apis/credentials")
        print("📖 Detailed guide: https://developers.google.com/youtube/v3/quickstart/python")
        print("="*80)
    
    def _get_credentials(self) -> Credentials:
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
                    )
                    
                    # Check if manual flow is forced or if we're in a headless environment
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
                        logger.info("Obtained new credentials via manual flow")
                        
                except Exception as e:
                    raise AuthenticationError(f"Failed to obtain new credentials: {e}")
        
        # Save credentials
        try:
            with open(self.config.youtube_credentials, 'w') as token:
                token.write(creds.to_json())
            logger.debug("Saved credentials to file")
        except Exception as e:
            logger.warning(f"Failed to save credentials: {e}")
        
        return creds
    
    def _print_setup_instructions(self):
        """Print detailed instructions for setting up YouTube API credentials."""
        print("\n" + "="*80)
        print("🔑 YOUTUBE API CREDENTIALS SETUP REQUIRED")
        print("="*80)
        print("The file 'client_secrets.json' is missing. Follow these steps to set it up:")
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
        print("   - Place it in the same directory as this application")
        print()
        print("6. 🚀 Run the application again")
        print("   - The first run will open a browser for authorization")
        print("   - Follow the prompts to authorize the application")
        print()
        print("📚 More info: https://developers.google.com/youtube/v3/getting-started")
        print("="*80)
        print()
    
    def _manual_oauth_flow(self, flow: InstalledAppFlow) -> Credentials:
        """
        Manual OAuth2 flow for headless environments.
        
        Args:
            flow: The OAuth2 flow object
            
        Returns:
            Valid credentials
            
        Raises:
            AuthenticationError: If manual flow fails
        """
        try:
            # Set redirect URI for manual flow
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            # Get the authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            print("\n" + "="*60)
            print("MANUAL YOUTUBE AUTHENTICATION REQUIRED")
            print("="*60)
            print("1. Open this URL in your browser:")
            print(f"   {auth_url}")
            print("\n2. Complete the authorization process")
            print("3. Copy the authorization code from the page")
            print("   (After authorization, you'll see a code on the page)")
            print("="*60)
            
            # Get authorization code from user
            auth_code = input("\nEnter the authorization code: ").strip()
            
            if not auth_code:
                raise AuthenticationError("No authorization code provided")
            
            # Exchange code for credentials
            flow.fetch_token(code=auth_code)
            return flow.credentials
            
        except Exception as e:
            raise AuthenticationError(f"Manual OAuth flow failed: {e}")
    
    def _build_service(self):
        """Build YouTube API service."""
        if not GOOGLE_APIS_AVAILABLE:
            raise YouTubeUploadError("Google API libraries not available")
        
        if not self.service or not self._credentials or not self._credentials.valid:
            self._credentials = self._get_credentials()
            self.service = build('youtube', 'v3', credentials=self._credentials)
            logger.debug("Built YouTube API service")
    
    def upload_video(self, file_path: str, title: str, description: str = "",
                    privacy: Optional[str] = None, category: Optional[str] = None,
                    tags: Optional[list] = None) -> Optional[str]:
        """
        Upload video to YouTube with retry logic.
        
        Args:
            file_path: Path to video file
            title: Video title
            description: Video description
            privacy: Privacy setting (private, public, unlisted)
            category: YouTube category ID
            tags: List of tags
            
        Returns:
            Video ID if successful, None otherwise
            
        Raises:
            YouTubeUploadError: If upload fails after retries
        """
        if not GOOGLE_APIS_AVAILABLE:
            logger.error("Cannot upload: Google API libraries not available")
            return None
        
        if not os.path.exists(file_path):
            raise YouTubeUploadError(f"Video file not found: {file_path}")
        
        # Check file size
        file_size = os.path.getsize(file_path) / (1024 ** 3)  # GB
        if file_size > self.config.max_file_size_gb:
            logger.warning(f"File size ({file_size:.2f}GB) exceeds limit ({self.config.max_file_size_gb}GB)")
        
        # Use defaults if not provided
        privacy = privacy or self.config.default_privacy
        category = category or self.config.default_category
        tags = tags or self.config.default_tags
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': category
            },
            'status': {
                'privacyStatus': privacy
            }
        }
        
        # Prepare media upload
        media = MediaFileUpload(
            file_path,
            chunksize=-1,  # Upload in single request
            resumable=True
        )
        
        for attempt in range(self.config.max_retries):
            try:
                self._build_service()
                
                logger.info(f"Uploading video (attempt {attempt + 1}/{self.config.max_retries}): {title}")
                
                request = self.service.videos().insert(
                    part=','.join(body.keys()),
                    body=body,
                    media_body=media
                )
                
                response = self._execute_upload(request)
                
                if response:
                    video_id = response['id']
                    logger.info(f"Successfully uploaded video: {video_id}")
                    return video_id
                
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    # Retriable HTTP errors
                    logger.warning(f"Retriable HTTP error {e.resp.status}: {e}")
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                else:
                    # Non-retriable error
                    raise YouTubeUploadError(f"HTTP error {e.resp.status}: {e}")
            
            except Exception as e:
                logger.error(f"Upload attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise YouTubeUploadError(f"Upload failed after {self.config.max_retries} attempts: {e}")
        
        return None
    
    def _execute_upload(self, request) -> Optional[Dict[str, Any]]:
        """
        Execute the upload request with progress tracking.
        
        Args:
            request: YouTube API upload request
            
        Returns:
            Upload response or None if failed
        """
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    logger.debug(f"Upload progress: {int(status.progress() * 100)}%")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = f"A retriable HTTP error {e.resp.status} occurred: {e.content}"
                else:
                    raise e
            except Exception as e:
                error = f"An error occurred: {e}"
            
            if error is not None:
                logger.warning(error)
                retry += 1
                if retry > self.config.max_retries:
                    logger.error("Upload failed after maximum retries")
                    return None
                
                max_sleep = 2 ** retry
                sleep_seconds = min(max_sleep, self.config.retry_delay)
                logger.info(f"Sleeping {sleep_seconds} seconds and then retrying...")
                time.sleep(sleep_seconds)
        
        return response
    
    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an uploaded video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video information dictionary
        """
        try:
            self._build_service()
            request = self.service.videos().list(
                part="snippet,status,statistics",
                id=video_id
            )
            response = request.execute()
            
            if response['items']:
                return response['items'][0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get video info for {video_id}: {e}")
            return None


class FallbackUploader:
    """
    Fallback uploader using external youtube-upload tool.
    """
    
    def __init__(self, config: VideoConfig):
        self.config = config
    
    def upload_video(self, file_path: str, title: str, description: str = "") -> bool:
        """
        Upload video using external youtube-upload tool.
        
        Args:
            file_path: Path to video file
            title: Video title
            description: Video description
            
        Returns:
            True if upload successful
        """
        import subprocess
        
        cmd = ["youtube-upload", "--title", title]
        if description:
            cmd.extend(["--description", description])
        cmd.append(file_path)
        
        logger.info(f"Using fallback uploader: {' '.join(cmd)}")
        
        for attempt in range(self.config.max_retries):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"Fallback upload successful: {result.stdout}")
                return True
            except subprocess.CalledProcessError as e:
                logger.warning(f"Fallback upload attempt {attempt + 1} failed: {e.stderr}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                    continue
                else:
                    logger.error(f"Fallback upload failed after {self.config.max_retries} attempts")
                    return False
        
        return False
