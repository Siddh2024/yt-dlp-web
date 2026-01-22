import yt_dlp
import os
import sys

# Test Video (Short, unlikely to get taken down, standard format)
URL = "https://www.youtube.com/watch?v=BaW_jenozKc" 

def test_download():
    cookie_file = 'cookies.txt'
    if not os.path.exists(cookie_file):
        print(f"ERROR: {cookie_file} not found!")
        return

    print(f"Using cookie file: {os.path.abspath(cookie_file)}")

    visitor_data = "CgtySjVsV2FvRFpYQSjT68bLBjIKCgJJThIEGgAgPA%3D%3D" # Hardcoded for verification
    
    # Basic options akin to what the app uses, but stripped down for debugging
    ydl_opts = {
        'cookiefile': cookie_file,
        'verbose': True,
        'no_warnings': False,
        'cache_dir': os.path.join(os.getcwd(), 'test_cache'),
        'outtmpl': 'test_download.%(ext)s',
        'extractor_args': {
            'youtube': {
                'player_client': ['android'], # Try android client with visitor data
                'visitor_data': [visitor_data]
            }
        }
    }

    try:
        print("Attempting to extract info...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([URL])
        print("SUCCESS: Download completed.")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    test_download()
