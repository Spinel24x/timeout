import os
import json
import uuid
import subprocess
import shutil
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()

# Generate or load UUID
UUID_FILE = '/usr/local/xray/current_uuid.txt'

def get_uuid():
    if os.path.exists(UUID_FILE):
        with open(UUID_FILE, 'r') as f:
            return f.read().strip()
    new_uuid = str(uuid.uuid4())
    with open(UUID_FILE, 'w') as f:
        f.write(new_uuid)
    return new_uuid

def update_xray_config(uuid):
    config_path = '/usr/local/xray/config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    config['inbounds'][0]['settings']['clients'] = [{
        "id": uuid,
        "level": 0
    }]
    config['inbounds'][0]['streamSettings']['wsSettings']['path'] = f'/{uuid}'
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Restart Xray
    os.system('pkill xray 2>/dev/null; sleep 1; /usr/local/xray/xray run -config /usr/local/xray/config.json &')
    
    return config

# Panel HTML
PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VLESS Panel - BPB Style</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #e2e8f0; min-height: 100vh; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; padding: 40px 0; }
        .header h1 { font-size: 32px; font-weight: 800; margin-bottom: 8px; background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header p { color: #94a3b8; font-size: 14px; }
        .card { background: #1e293b; border-radius: 16px; padding: 24px; margin-bottom: 20px; border: 1px solid #334155; }
        .card h2 { font-size: 18px; margin-bottom: 16px; color: #f1f5f9; }
        .form-group { margin-bottom: 16px; }
        label { display: block; font-size: 12px; font-weight: 700; color: #94a3b8; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        input, select, textarea { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #e2e8f0; font-size: 14px; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #6366f1; }
        textarea { resize: vertical; min-height: 80px; font-family: monospace; }
        .btn { width: 100%; padding: 12px; background: #6366f1; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn:hover { background: #4f46e5; transform: translateY(-1px); }
        .btn-green { background: #22c55e; }
        .btn-green:hover { background: #16a34a; }
        .result { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 16px; margin-top: 16px; font-family: monospace; font-size: 12px; word-break: break-all; display: none; }
        .result.show { display: block; }
        .tabs { display: flex; gap: 8px; margin-bottom: 20px; }
        .tab { flex: 1; padding: 10px; text-align: center; background: #1e293b; border: 1px solid #334155; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; }
        .tab.active { background: #6366f1; border-color: #6366f1; color: white; }
        .hidden { display: none; }
        .info-box { background: #1e3a5f; border: 1px solid #3b82f6; border-radius: 8px; padding: 12px; margin-top: 16px; font-size: 12px; color: #93c5fd; }
        .status { padding: 8px 12px; border-radius: 6px; margin-top: 12px; font-size: 13px; text-align: center; }
        .status.online { background: #065f46; color: #6ee7b7; }
        .status.offline { background: #7f1d1d; color: #fca5a5; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 VLESS Panel</h1>
            <p>Cloudflare Worker → Railway Xray</p>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="switchTab('login')">Login</div>
            <div class="tab" onclick="switchTab('panel')">Panel</div>
        </div>

        <div id="login-tab">
            <div class="card">
                <h2>Login</h2>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="password" placeholder="Enter password">
                </div>
                <button class="btn" onclick="login()">Login</button>
                <div id="login-status"></div>
            </div>
        </div>

        <div id="panel-tab" class="hidden">
            <div class="card">
                <h2>Generate VLESS Config</h2>
                <div class="form-group">
                    <label>Remark</label>
                    <input type="text" id="remark" value="VLESS-WS-TLS" placeholder="Config name">
                </div>
                <div class="form-group">
                    <label>Clean IPs (one per line)</label>
                    <textarea id="cleanips" placeholder="104.26.0.1&#10;104.26.1.1"></textarea>
                </div>
                <div class="form-group">
                    <label>Port</label>
                    <select id="port">
                        <option value="443">443</option>
                        <option value="8443">8443</option>
                        <option value="2053">2053</option>
                        <option value="2083">2083</option>
                        <option value="2087">2087</option>
                        <option value="2096">2096</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Domain (Worker/Custom)</label>
                    <input type="text" id="domain" placeholder="your-domain.com">
                </div>
                <button class="btn" onclick="generateConfig()">Generate Config</button>
                <div id="result" class="result">
                    <div id="config-text"></div>
                    <button class="btn btn-green" style="margin-top:12px;" onclick="copyConfig()">Copy Config</button>
                </div>
                <div class="info-box">⚡ TLS is handled by Cloudflare. Xray runs WS (no TLS) on Railway. Worker proxies all traffic.</div>
            </div>
        </div>
    </div>

    <script>
        let isLoggedIn = false;
        let currentConfig = '';

        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById('login-tab').classList.add('hidden');
            document.getElementById('panel-tab').classList.add('hidden');
            if (tab === 'login') {
                document.querySelector('.tab:first-child').classList.add('active');
                document.getElementById('login-tab').classList.remove('hidden');
            } else {
                if (!isLoggedIn) { alert('Please login first!'); return; }
                document.querySelector('.tab:last-child').classList.add('active');
                document.getElementById('panel-tab').classList.remove('hidden');
            }
        }

        async function login() {
            const password = document.getElementById('password').value;
            const statusEl = document.getElementById('login-status');
            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password })
                });
                const data = await res.json();
                if (data.success) {
                    isLoggedIn = true;
                    localStorage.setItem('panel_pass', password);
                    statusEl.innerHTML = '<div class="status online">✅ Login successful!</div>';
                    setTimeout(() => switchTab('panel'), 500);
                } else {
                    statusEl.innerHTML = '<div class="status offline">❌ Wrong password!</div>';
                }
            } catch (err) {
                statusEl.innerHTML = '<div class="status offline">❌ Connection error!</div>';
            }
        }

        async function generateConfig() {
            const password = localStorage.getItem('panel_pass') || document.getElementById('password').value;
            const remark = document.getElementById('remark').value;
            const cleanips = document.getElementById('cleanips').value.split('\\n').filter(ip => ip.trim());
            const port = document.getElementById('port').value;
            const domain = document.getElementById('domain').value;

            if (!domain) { alert('Please enter domain!'); return; }

            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password, remark, cleanips, port, domain })
                });
                const data = await res.json();
                if (data.error) { alert(data.error); return; }
                currentConfig = data.config;
                document.getElementById('config-text').textContent = currentConfig;
                document.getElementById('result').classList.add('show');
            } catch (err) {
                alert('Error: ' + err.message);
            }
        }

        function copyConfig() {
            navigator.clipboard.writeText(currentConfig).then(() => alert('Copied!'));
        }

        // Check if already logged in
        if (localStorage.getItem('panel_pass')) {
            document.getElementById('password').value = localStorage.getItem('panel_pass');
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return PANEL_HTML

@app.post("/api/login")
async def login(request: Request):
    try:
        body = await request.json()
        password = body.get('password', '')
        panel_pass = os.environ.get('WP', 'admin123')
        if password == panel_pass:
            return {"success": True}
        return JSONResponse({"success": False, "error": "Wrong password"}, status_code=401)
    except:
        return JSONResponse({"success": False, "error": "Invalid request"}, status_code=400)

@app.post("/api/generate")
async def generate(request: Request):
    try:
        body = await request.json()
        password = body.get('password', '')
        panel_pass = os.environ.get('WP', 'admin123')
        
        if password != panel_pass:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
        new_uuid = str(uuid.uuid4())
        update_xray_config(new_uuid)
        
        remark = body.get('remark', 'VLESS-WS-TLS')
        cleanips = body.get('cleanips', [])
        port = body.get('port', 443)
        domain = body.get('domain', '')
        
        if not domain:
            return JSONResponse({"error": "Domain is required"}, status_code=400)
        
        ips = cleanips if cleanips else [domain]
        configs = []
        
        for i, ip in enumerate(ips):
            name = f"{remark}-{i+1}" if len(ips) > 1 else remark
            config = f"vless://{new_uuid}@{ip.strip()}:{port}?type=ws&security=tls&path=/{new_uuid}&host={domain}&sni={domain}&fp=chrome&alpn=http/1.1&encryption=none#{name}"
            configs.append(config)
        
        return {
            "success": True,
            "config": '\n\n'.join(configs),
            "uuid": new_uuid,
            "details": {
                "uuid": new_uuid,
                "host": domain,
                "port": port,
                "path": f"/{new_uuid}",
                "type": "ws",
                "security": "tls",
                "fingerprint": "chrome",
                "alpn": "http/1.1"
            }
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "xray": "running"}

if __name__ == "__main__":
    # Start Xray on startup
    current_uuid = get_uuid()
    update_xray_config(current_uuid)
    print(f"Xray started with UUID: {current_uuid}")
    
    # Start FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8080)
