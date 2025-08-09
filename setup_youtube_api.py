#!/usr/bin/env python3
"""
YouTube API Setup Helper

This script helps users set up their YouTube API credentials by providing
detailed step-by-step instructions and checking for the required files.
"""
import os
import sys
import webbrowser
from pathlib import Path


def print_header():
    """Print the script header."""
    print("\n" + "="*80)
    print("🎥 YOUTUBE VIDEO UPLOADER - API SETUP HELPER")
    print("="*80)
    print("This script will guide you through setting up YouTube API credentials.")
    print()


def check_current_setup():
    """Check the current setup status."""
    print("🔍 Checking current setup...")
    print()
    
    client_secrets_exists = os.path.exists("client_secrets.json")
    youtube_credentials_exists = os.path.exists("youtube_credentials.json")
    
    print(f"📄 client_secrets.json: {'✅ Found' if client_secrets_exists else '❌ Missing'}")
    print(f"🔐 youtube_credentials.json: {'✅ Found' if youtube_credentials_exists else '❌ Missing (will be created after first auth)'}")
    print()
    
    if client_secrets_exists:
        print("🎉 Great! Your client_secrets.json file is already set up.")
        if not youtube_credentials_exists:
            print("💡 Run the main application to complete the OAuth authorization.")
        else:
            print("✨ Your YouTube API setup is complete!")
        return True
    
    return False


def print_detailed_instructions():
    """Print detailed setup instructions."""
    print("📋 DETAILED SETUP INSTRUCTIONS")
    print("="*50)
    print()
    
    print("STEP 1: 🌐 Go to Google Cloud Console")
    print("   URL: https://console.cloud.google.com/")
    print("   This is Google's platform for managing API access.")
    print()
    
    print("STEP 2: 📁 Create or select a project")
    print("   - Look for 'Select a project' dropdown at the top of the page")
    print("   - If you don't have a project:")
    print("     * Click 'NEW PROJECT'")
    print("     * Give it a name (e.g., 'YouTube Uploader')")
    print("     * Click 'CREATE'")
    print("   - If you have projects, select one or create a new one")
    print()
    
    print("STEP 3: 🔌 Enable YouTube Data API v3")
    print("   - In the left sidebar, go to 'APIs & Services' > 'Library'")
    print("   - In the search box, type 'YouTube Data API v3'")
    print("   - Click on 'YouTube Data API v3' from the results")
    print("   - Click the blue 'ENABLE' button")
    print("   - Wait for it to enable (may take a few seconds)")
    print()
    
    print("STEP 4: 🔐 Create OAuth 2.0 credentials")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click the blue '+ CREATE CREDENTIALS' button")
    print("   - Select 'OAuth client ID' from the dropdown")
    print("   - If prompted about OAuth consent screen:")
    print("     * Click 'CONFIGURE CONSENT SCREEN'")
    print("     * Choose 'External' (unless you have a Google Workspace)")
    print("     * Fill in required fields (App name, User support email, etc.)")
    print("     * You can skip most optional fields")
    print("     * Save and continue through the steps")
    print("   - For Application type, choose 'Desktop application'")
    print("   - Give it a name (e.g., 'YouTube Video Uploader')")
    print("   - Click 'CREATE'")
    print()
    
    print("STEP 5: 💾 Download the credentials")
    print("   - You'll see a popup with your client ID and secret")
    print("   - Click 'DOWNLOAD JSON' button")
    print("   - OR go back to the credentials list:")
    print("     * Find your OAuth 2.0 Client IDs")
    print("     * Click the download button (⬇️) on the right side")
    print("   - Save the file and rename it to 'client_secrets.json'")
    print("   - Move this file to the same directory as this script")
    print()
    
    print("STEP 6: 🚀 Run the uploader")
    print("   - Once you have client_secrets.json in place, run the main application")
    print("   - The first time will open a browser for authorization")
    print("   - Sign in with your YouTube/Google account")
    print("   - Grant the requested permissions")
    print("   - The application will save the authorization for future use")
    print()
    
    print("📚 Additional Resources:")
    print("   - YouTube API Documentation: https://developers.google.com/youtube/v3/getting-started")
    print("   - Google Cloud Console: https://console.cloud.google.com/")
    print("   - OAuth 2.0 Guide: https://developers.google.com/identity/protocols/oauth2")
    print()


def offer_to_open_browser():
    """Offer to open the Google Cloud Console in browser."""
    print("🌐 QUICK ACCESS")
    print("="*20)
    response = input("Would you like me to open Google Cloud Console in your browser? (y/n): ").strip().lower()
    
    if response in ['y', 'yes', '1']:
        try:
            webbrowser.open('https://console.cloud.google.com/')
            print("✅ Opened Google Cloud Console in your browser!")
        except Exception as e:
            print(f"❌ Could not open browser: {e}")
            print("Please manually go to: https://console.cloud.google.com/")
    else:
        print("💡 You can manually go to: https://console.cloud.google.com/")
    print()


def wait_for_file():
    """Wait for the user to place the client_secrets.json file."""
    print("⏳ WAITING FOR FILE")
    print("="*20)
    print("Once you've downloaded client_secrets.json and placed it in this directory,")
    print("press Enter to check again, or 'q' to quit.")
    
    while True:
        response = input("\nPress Enter to check for client_secrets.json (or 'q' to quit): ").strip().lower()
        
        if response == 'q':
            print("👋 Goodbye! Run this script again when you're ready to continue.")
            return False
        
        if os.path.exists("client_secrets.json"):
            print("🎉 Found client_secrets.json! Setup is complete.")
            print("✨ You can now run the main YouTube uploader application.")
            return True
        else:
            print("❌ client_secrets.json not found. Please make sure:")
            print("   - The file is named exactly 'client_secrets.json'")
            print("   - It's in the same directory as this script")
            print(f"   - Current directory: {os.getcwd()}")


def main():
    """Main function."""
    print_header()
    
    # Check current setup
    if check_current_setup():
        return
    
    print("🛠️  Let's set up your YouTube API credentials!")
    print()
    
    # Print detailed instructions
    print_detailed_instructions()
    
    # Offer to open browser
    offer_to_open_browser()
    
    # Wait for user to complete setup
    if wait_for_file():
        print("\n🎉 Setup complete! You can now use the YouTube Video Uploader.")
        print("💡 The first run will require browser authorization to complete the setup.")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user. Run the script again when ready!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)
