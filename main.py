import os
import json
import uuid
import subprocess
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI()

XRAY_CONFIG = '/usr/local/xray/config.json'
XRAY_PORT = 10000  # Xray direct port
PANEL_PORT = 8080  # Panel port

def restart_xray(uuid_val):
    """Update Xray config with new UUID and restart"""
    config = {
        "log": {"loglevel": "warning"},
        "inbounds": [{
            "port": XRAY_PORT,
            "listen": "0.0.0.0",
            "protocol": "vless",
            "settings": {
                "clients": [{"id": uuid_val, "level": 0}],
                "decryption": "none"
            },
            "streamSettings": {
                "network": "ws",
                "security": "none",
                "wsSettings": {
                    "path": f"/{uuid_val}",
                    "headers": {}
                }
            },
            "tag": "vless-in"
        }],
        "outbounds": [{
            "protocol": "freedom",
            "settings": {},
            "tag": "direct"
        }]
    }
    
    with open(XRAY_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Kill and restart Xray
    subprocess.run('pkill -f "xray run" 2>/dev/null || true', shell=True)
    subprocess.Popen(['/usr/local/xray/xray', 'run', '-config', XRAY_CONFIG],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True

PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VLESS Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { max-width: 500px; width: 90%; margin: 20px; }
        .card { background: #1e293b; border-radius: 16px; padding: 30px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }
        h1 { font-size: 24px; font-weight: 700; text-align: center; color: #f1f5f9; margin-bottom: 4px; }
        .subtitle { text-align: center; color: #94a3b8; margin-bottom: 24px; font-size: 13px; }
        .form-group { margin-bottom: 18px; }
        label { display: block; font-size: 12px; font-weight: 700; color: #94a3b8; margin-bottom: 6px; text-transform: uppercase; }
        input, select, textarea { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #e2e8f0; font-size: 14px; }
        input:focus, select:focus, textarea:focus { outline: none; border-color: #6366f1; }
        textarea { resize: vertical; min-height: 70px; font-family: monospace; }
        .btn { width: 100%; padding: 14px; background: #6366f1; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; margin-top: 8px; }
        .btn:hover { background: #4f46e5; }
        .btn-green { background: #22c55e; margin-top: 12px; }
        .btn-green:hover { background: #16a34a; }
        .result { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 16px; margin-top: 16px; font-family: monospace; font-size: 12px; word-break: break-all; display: none; line-height: 1.6; }
        .result.show { display: block; }
        .tabs { display: flex; gap: 8px; margin-bottom: 20px; }
        .tab { flex: 1; padding: 10px; text-align: center; background: #1e293b; border: 1px solid #334155; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; color: #94a3b8; }
        .tab.active { background: #6366f1; border-color: #6366f1; color: white; }
        .hidden { display: none; }
        .status { padding: 10px; border-radius: 8px; margin-top: 12px; font-size: 13px; text-align: center; }
        .status.success { background: #065f46; color: #6ee7b7; }
        .status.error { background: #7f1d1d; color: #fca5a5; }
        .info-box { background: #1e3a5f; border: 1px solid #3b82f6; border-radius: 8px; padding: 12px; margin-top: 16px; font-size: 12px; color: #93c5fd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>VLESS Panel</h1>
            <p class="subtitle">Worker → Railway:10000 (Xray) | Panel:8080</p>
            
            <div class="tabs">
                <div class="tab active" onclick="switchTab('login')">Login</div>
                <div class="tab" onclick="switchTab('panel')">Panel</div>
            </div>

            <div id="login-tab">
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="password" placeholder="Enter password">
                </div>
                <button class="btn" onclick="login()">Login</button>
                <div id="login-status"></div>
            </div>

            <div id="panel-tab" class="hidden">
                <div class="form-group">
                    <label>Remark</label>
                    <input type="text" id="remark" value="VLESS-WS-TLS">
                </div>
                <div class="form-group">
                    <label>Clean IPs (optional)</label>
                    <textarea id="cleanips" placeholder="104.26.0.1&#10;104.26.1.1"></textarea>
                </div>
                <div class="form-group">
                    <label>Port (for client)</label>
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
                    <label>Worker Domain (WD)</label>
                    <input type="text" id="domain" placeholder="panel.yourname.workers.dev">
                </div>
                <button class="btn" onclick="generateConfig()">Generate Config</button>
                
                <div id="result" class="result">
                    <div id="config-text"></div>
                    <button class="btn btn-green" onclick="copyConfig()">📋 Copy Config</button>
                </div>
                
                <div class="info-box">
                    💡 Architecture: Client → Cloudflare Worker → Railway:10000 (Xray WS)<br>
                    Panel runs on Railway:8080 (HTTP only)
                </div>
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
                    localStorage.setItem('pass', password);
                    statusEl.innerHTML = '<div class="status success">✅ Success!</div>';
                    setTimeout(() => switchTab('panel'), 500);
                } else {
                    statusEl.innerHTML = '<div class="status error">❌ Wrong password!</div>';
                }
            } catch (err) {
                statusEl.innerHTML = '<div class="status error">❌ Error!</div>';
            }
        }

        async function generateConfig() {
            const password = localStorage.getItem('pass') || document.getElementById('password').value;
            const remark = document.getElementById('remark').value || 'VLESS';
            const cleanips = document.getElementById('cleanips').value.split('\\n').filter(ip => ip.trim());
            const port = document.getElementById('port').value;
            const domain = document.getElementById('domain').value.trim();

            if (!domain) { alert('Enter Worker Domain!'); return; }

            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password, remark, cleanips, port: parseInt(port), domain })
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

        if (localStorage.getItem('pass')) {
            document.getElementById('password').value = localStorage.getItem('pass');
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return PANEL_HTML

@app.get("/health")
async def health():
    return {"status": "ok", "xray_port": XRAY_PORT, "panel_port": PANEL_PORT}

@app.post("/api/login")
async def login(request: Request):
    try:
        body = await request.json()
        password = body.get('password', '')
        panel_pass = os.environ.get('WP', 'admin123')
        if str(password) == str(panel_pass):
            return {"success": True}
        return JSONResponse({"success": False, "error": "Wrong password"}, status_code=401)
    except:
        return JSONResponse({"success": False, "error": "Invalid"}, status_code=400)

@app.post("/api/generate")
async def generate(request: Request):
    try:
        body = await request.json()
        password = body.get('password', '')
        panel_pass = os.environ.get('WP', 'admin123')
        
        if str(password) != str(panel_pass):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
        new_uuid = str(uuid.uuid4())
        restart_xray(new_uuid)
        
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
            c = f"vless://{new_uuid}@{ip.strip()}:{port}?type=ws&security=tls&path=/{new_uuid}&host={domain}&sni={domain}&fp=chrome&alpn=http/1.1&encryption=none#{name}"
            configs.append(c)
        
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

if __name__ == "__main__":
    print(f"Panel on port {PANEL_PORT}")
    print(f"Xray on port {XRAY_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PANEL_PORT)
