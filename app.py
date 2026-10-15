import os
import secrets
import subprocess
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_file, after_this_request

app = Flask(__name__)
MAX_MINUTES = int(os.getenv('MAX_MINUTES', '15'))
TOKEN = os.getenv('API_TOKEN', '')

@app.get('/')
def status():
    return jsonify(service='mp3-test', status='running', note='Only use media you have permission to download.')

@app.post('/convert')
def convert():
    if not TOKEN or not secrets.compare_digest(request.headers.get('X-API-Token', ''), TOKEN):
        return jsonify(error='Unauthorized'), 401
    data = request.get_json(silent=True) or {}
    url = data.get('url', '')
    if not isinstance(url, str) or len(url) > 500 or not (url.startswith('https://www.youtube.com/watch?v=') or url.startswith('https://youtu.be/') or url.startswith('https://www.youtube.com/shorts/')):
        return jsonify(error='Use a supported YouTube URL.'), 400
    tmp = tempfile.TemporaryDirectory(prefix='mp3job_')
    base = Path(tmp.name)
    try:
        # No playlists; cap duration BEFORE attempting a download. Commands are passed as argv, not a shell.
        cmd = ['yt-dlp', '--no-playlist', '--max-downloads', '1', '--match-filter', f'duration <= {MAX_MINUTES * 60} & duration != NA',
               '--no-progress', '--no-warnings', '--socket-timeout', '10', '--retries', '1', '--fragment-retries', '1',
               '-x', '--audio-format', 'mp3', '--audio-quality', '5', '-o', str(base / 'audio.%(ext)s'), url]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False)
        output = base / 'audio.mp3'
        if p.returncode != 0 or not output.exists():
            tmp.cleanup()
            return jsonify(error='Conversion failed or video is unsupported.', detail=p.stderr[-700:]), 422
        @after_this_request
        def cleanup(response):
            response.call_on_close(tmp.cleanup)
            return response
        return send_file(output, mimetype='audio/mpeg', as_attachment=True, download_name='ses.mp3')
    except subprocess.TimeoutExpired:
        tmp.cleanup()
        return jsonify(error='Time limit exceeded.'), 504
    except Exception:
        tmp.cleanup()
        return jsonify(error='Unexpected processing error.'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '10000')))
