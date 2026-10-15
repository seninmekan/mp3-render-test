import os
import secrets
import subprocess
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_file, after_this_request, render_template_string

app = Flask(__name__)
MAX_MINUTES = int(os.getenv('MAX_MINUTES', '15'))
TOKEN = os.getenv('API_TOKEN', '')

PAGE = '''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Render MP3 Testi</title><style>body{font:16px system-ui;background:#101419;color:#f4f7fc;margin:0;padding:40px 15px}.panel{max-width:540px;margin:5vh auto;background:#1c222b;padding:28px;border-radius:16px}input,button{box-sizing:border-box;width:100%;padding:14px;border-radius:9px;margin:8px 0 18px;font:inherit}input{background:#101419;color:white;border:1px solid #4b586a}button{background:#a9e5b6;border:0;font-weight:700;cursor:pointer}small{color:#bac6d7}#message{white-space:pre-wrap}</style></head><body><main class="panel"><h1>Render MP3 Testi</h1><p>Bu sayfa doğrudan Render sunucusunda çalışır. Bilgisayarına yardımcı program kurulmaz.</p><form id="frm"><label>YouTube bağlantısı<input required id="url" type="url" placeholder="https://www.youtube.com/watch?v=..."></label><label>Render API_TOKEN<input required id="token" type="password" autocomplete="off" placeholder="Gizli anahtar"></label><button id="go">MP3 oluştur ve indir</button></form><p id="message"></p><small>Test sürümü. Yalnızca indirme iznin olan içeriklerle dene. Anahtar bu sayfada kaydedilmez. 15 dakika sınırı vardır.</small></main><script>document.getElementById('frm').addEventListener('submit', async e=>{e.preventDefault();const go=document.getElementById('go'),msg=document.getElementById('message');go.disabled=true;msg.textContent='Render işlem yapıyor, lütfen bekle...';try{const res=await fetch('/convert',{method:'POST',headers:{'Content-Type':'application/json','X-API-Token':document.getElementById('token').value},body:JSON.stringify({url:document.getElementById('url').value})});if(!res.ok){const x=await res.json().catch(()=>({error:'HTTP '+res.status}));throw Error((x.error||'Hata')+(x.detail?'\n'+x.detail:''))}const blob=await res.blob();const u=URL.createObjectURL(blob);const a=document.createElement('a');a.href=u;a.download='ses.mp3';a.click();setTimeout(()=>URL.revokeObjectURL(u),60000);msg.textContent='MP3 indirme başlatıldı ('+(blob.size/1024/1024).toFixed(1)+' MB).'}catch(err){msg.textContent='HATA: '+err.message}finally{go.disabled=false}})</script></body></html>'''

@app.get('/')
def status():
    return jsonify(service='mp3-test', status='running', note='Only use media you have permission to download.')

@app.get('/test')
def test_page():
    response = app.make_response(render_template_string(PAGE))
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

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
        cmd = ['yt-dlp', '--no-playlist', '--max-downloads', '1', '--match-filter', f'duration <= {MAX_MINUTES * 60} & duration != NA', '--no-progress', '--no-warnings', '--socket-timeout', '10', '--retries', '1', '--fragment-retries', '1', '-x', '--audio-format', 'mp3', '--audio-quality', '5', '-o', str(base / 'audio.%(ext)s'), url]
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
