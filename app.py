from flask import Flask, render_template, request, Response, jsonify, send_from_directory
import os
from downloader import Downloader
import threading
import json
import time
import queue

app = Flask(__name__)
message_queue = queue.Queue()
is_downloading = False

def status_callback(data):
    """
    Push data to the queue for the SSE consumer.
    """
    message_queue.put(data)

HISTORY_FILE = 'history.json'

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history_item(item):
    history = load_history()
    # Add to start
    history.insert(0, item)
    # Limit to last 50
    history = history[:50]
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def get_history():
    return jsonify(load_history())

@app.route('/download', methods=['POST'])
def start_download():
    global is_downloading
    if is_downloading:
        return jsonify({'status': 'error', 'message': 'Download already in progress'}), 400

    data = request.json
    url = data.get('url')
    fmt = data.get('format')

    if not url:
        return jsonify({'status': 'error', 'message': 'No URL provided'}), 400

    # Clear queue
    with message_queue.mutex:
        message_queue.queue.clear()

    downloader = Downloader()
    
    def target():
        global is_downloading
        is_downloading = True
        
        # Inject our history saver into the callback wrapper
        def wrapped_callback(data):
            if data.get('status') == 'finished':
                # Save to history when finished
                save_history_item({
                    'title': data.get('filename'), # Fallback title, ideally we get real title
                    'url': url,
                    'format': fmt,
                    'date': time.strftime("%Y-%m-%d %H:%M"),
                    'filename': data.get('filename')
                })
            status_callback(data)

        downloader.download_video(url, fmt, wrapped_callback)
        is_downloading = False

    thread = threading.Thread(target=target, daemon=True)
    thread.start()

    return jsonify({'status': 'started'})

@app.route('/progress')
def progress():
    def generate():
        while True:
            try:
                # Wait for data with a timeout to keep connection alive
                data = message_queue.get(timeout=30) 
                yield f"data: {json.dumps(data)}\n\n"
                
                if data.get('status') in ['finished', 'error']:
                    break
            except queue.Empty:
                # Keep-alive heartbeat
                yield f"data: {json.dumps({'keep_alive': True})}\n\n"
            except GeneratorExit:
                break
    
    return Response(generate(), mimetype='text/event-stream')

from flask import Flask, render_template, request, Response, jsonify, send_from_directory
import os

# ... (imports remain the same, adding send_from_directory)

@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory('downloads', filename, as_attachment=True)

if __name__ == '__main__':
    # host='0.0.0.0' allows access from other devices on the network
    app.run(debug=True, host='0.0.0.0', port=5000)
