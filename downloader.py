import yt_dlp
import os
import time

class Downloader:
    def __init__(self, download_folder="downloads"):
        self.download_folder = download_folder
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
        self.active_progress = {}

    def format_bytes(self, size):
        power = 2**10
        n = 0
        power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size > power:
            size /= power
            n += 1
        return f"{size:.2f} {power_labels.get(n, '')}B"

    def format_seconds(self, seconds):
        if seconds is None:
            return "--:--"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{int(h):d}:{int(m):02d}:{int(s):02d}"
        return f"{int(m):02d}:{int(s):02d}"

    def progress_hook(self, d, callback=None):
        """
        Callback for yt-dlp to report progress.
        Normalizes data and invokes the external callback (e.g., to update simple queue).
        """




        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                
                if total > 0:
                    percentage = (downloaded / total) * 100
                else:
                    percentage = 0

                speed_raw = d.get('speed') # bytes/sec
                eta_raw = d.get('eta') # seconds
                
                speed_str = f"{self.format_bytes(speed_raw)}/s" if speed_raw else "N/A"
                eta_str = self.format_seconds(eta_raw)
                
                progress_data = {
                    'status': 'downloading',
                    'percentage': round(percentage, 1),
                    'percentage_str': f"{percentage:.1f}%",
                    'speed': speed_str,
                    'eta': eta_str,
                    'downloaded': self.format_bytes(downloaded),
                    'total': self.format_bytes(total),
                    'filename': d.get('filename', 'Unknown')
                }
                
                if callback:
                    callback(progress_data)
                    
            except Exception as e:
                print(f"Error in progress hook: {e}")

        elif d['status'] == 'finished':
            progress_data = {
                'status': 'processing', # It's finished downloading, but might be merging
                'percentage': 100,
                'percentage_str': "100%",
                'speed': "-",
                'eta': "Done",
                'message': "Processing/Merging..."
            }
            if callback:
                callback(progress_data)

    def download_video(self, url, format_type, callback):
        """
        url: Video URL
        format_type: 'video' or 'audio'
        callback: function(data) to receive updates
        """
        
        # 1. Check for Render Secret File
        cookie_file = None
        if os.path.exists('/etc/secrets/cookies.txt'):
            cookie_file = '/etc/secrets/cookies.txt'
        
        # 2. Check for local file
        elif os.path.exists('cookies.txt'):
            cookie_file = 'cookies.txt'
            
        # 3. Fallback: Create from Env Var (if small enough to not crash)
        elif os.environ.get('COOKIES_CONTENT'):
             with open('cookies.txt', 'w') as f:
                 f.write(os.environ.get('COOKIES_CONTENT'))
             cookie_file = 'cookies.txt'
        
        class QueueLogger:
            def __init__(self, callback):
                self.callback = callback
            def debug(self, msg):
                if self.callback and msg.startswith('[debug] '):
                     self.callback({'status': 'preparing', 'message': msg[:50]})
            def info(self, msg):
                if self.callback:
                    # Capture useful status messages that are NOT download progress
                    if not msg.startswith('[download]'):
                         self.callback({'status': 'preparing', 'message': msg})
            def warning(self, msg): pass
            def error(self, msg): pass

        ydl_opts = {
            'outtmpl': os.path.join(self.download_folder, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: self.progress_hook(d, callback)],
            'quiet': False, # Turn off quiet to generate logs
            'no_warnings': True,
            'logger': QueueLogger(callback),
            'verbose': True, 
            'cache_dir': '/tmp/yt-dlp-cache',
            'extractor_args': {'youtube': {'player_client': ['tv']}},
            'force_ipv4': True,
            'overwrites': True,
            'updatetime': False, # no_mtime equivalent, prevents FS errors
        }

        # FINAL ATTEMPT CONFIG:
        # 'tv' client uses a different API that is often less throttled on servers.

        if cookie_file:
            ydl_opts['cookiefile'] = cookie_file

        if format_type == 'audio_best':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
            })
        elif format_type == 'audio_low':
            ydl_opts.update({
                'format': 'worstaudio/worst',
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
            })
        elif format_type == 'video_1080':
            ydl_opts.update({'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'})
        elif format_type == 'video_720':
            ydl_opts.update({'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]'})
        elif format_type == 'video_480':
            ydl_opts.update({'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]'})
        elif format_type == 'video_only':
             ydl_opts.update({'format': 'bestvideo'})
        else:
            # Default: Best Video + Best Audio
            ydl_opts.update({'format': 'bestvideo+bestaudio/best'})

        def attempt_download(opts, client_name):
             if callback:
                callback({'status': 'preparing', 'message': f'Starting extraction ({client_name})...'})
             
             with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info

        po_token = os.environ.get('PO_TOKEN')
        visitor_data = os.environ.get('VISITOR_DATA')
        
        def get_args(client):
            args = {'player_client': [client]}
            if po_token and client == 'web':
                 args['po_token'] = [f"web+{po_token}"]
            if visitor_data:
                args['visitor_data'] = [visitor_data]
            return {'youtube': args}

        info = None
        
        # 0. Priority Attempt: Web Client with PO Token
        if po_token:
            try:
                print("DEBUG: PO Token detected, prioritizing Web Client.")
                ydl_opts['extractor_args'] = get_args('web')
                info = attempt_download(ydl_opts, "Web Client (with PO Token)")
            except Exception as e:
                print(f"PO Token Web attempt failed: {e}")
                if callback:
                    callback({'status': 'preparing', 'message': 'PO Token attempt failed, trying fallbacks...'})
        
        # Standard Fallback Loop if no info yet
        if not info:
            try:
                # 1. Android Client
                ydl_opts['extractor_args'] = get_args('android')
                info = attempt_download(ydl_opts, "Android Client")
            except Exception as e_android:
                print(f"Android Client failed: {e_android}")
                if callback:
                    callback({'status': 'preparing', 'message': 'Android Client failed, trying iOS...'})
                
                try:
                    # 2. iOS Client
                    ydl_opts['extractor_args'] = get_args('ios')
                    info = attempt_download(ydl_opts, "iOS Client")
                except Exception as e_ios:
                    print(f"iOS Client failed: {e_ios}")
                    if callback:
                        callback({'status': 'preparing', 'message': 'iOS Client failed, trying Web...'})
                    
                    # 3. Web Client (Last Resort)
                    ydl_opts['extractor_args'] = get_args('web')
                    info = attempt_download(ydl_opts, "Web Client")

        # Process the result (info)
        if info:
            # Parse filename to serve back to user
            if 'requested_downloads' in info:
                # Logic for merged formats
                final_filename = info['requested_downloads'][0]['filepath']
            else:
                # Logic for single file downloads
                final_filename = ydl.prepare_filename(info)
                
                # Correction for audio conversion (webm -> mp3) happens in post-process, 
                # but yt-dlp info might still say webm/m4a initially.
                if format_type == 'audio':
                        base, _ = os.path.splitext(final_filename)
                        final_filename = f"{base}.mp3"

            # Get just the basename to send to frontend
            basename = os.path.basename(final_filename)
            
            # Send final 'finished' status with filename
            callback({
                'status': 'finished',
                'percentage': 100,
                'message': "Download Complete!",
                'filename': basename
            })
            
