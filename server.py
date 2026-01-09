from gevent import monkey
monkey.patch_all()

from gevent.pywsgi import WSGIServer
from app import app
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Gevent WSGI Server on port {port}...")
    http_server = WSGIServer(('0.0.0.0', port), app)
    http_server.serve_forever()
