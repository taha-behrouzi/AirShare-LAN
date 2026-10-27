import os
import re
import http.server
import socket
import socketserver
import urllib.parse
import secrets
import email
import email.policy
import webbrowser
import threading

# Configuration
PORT = 8080
SHARED_DIR = os.path.join(os.path.abspath(os.getcwd()), "shared_files")
AUTH_TOKEN = secrets.token_urlsafe(16)

# Ensure the dedicated shared directory exists
if not os.path.exists(SHARED_DIR):
    os.makedirs(SHARED_DIR)

def get_local_ip():
    """Get the local network IP address of the machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def print_qr_code(url):
    """Generate and print a terminal QR code for easy mobile access."""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        print("\n" + "="*50)
        print(" SCAN THIS QR CODE WITH YOUR PHONE:")
        print("="*50 + "\n")
        qr.print_ascii(invert=True)
    except ImportError:
        print(f"\nDirect Access URL: {url}\n")

class SecureAirShareHandler(http.server.SimpleHTTPRequestHandler):
    
    def verify_request_token(self):
        """Verify that the request contains the valid security token."""
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        token_list = query_params.get('token', [])
        if token_list and token_list[0] == AUTH_TOKEN:
            return True
        return False

    def send_forbidden(self):
        """Send a 403 Forbidden response for unauthorized access attempts."""
        self.send_response(403)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        error_html = """<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>403 Forbidden</title>
            <style>
                body { background: #090d16; color: #f8fafc; font-family: system-ui, sans-serif; text-align: center; padding-top: 100px; }
                h1 { color: #f43f5e; font-size: 2.5rem; margin-bottom: 10px; }
                p { color: #94a3b8; font-size: 1.1rem; }
            </style>
        </head>
        <body>
            <h1>403 Access Denied</h1>
            <p>Invalid or missing security token. Please use the official secure link.</p>
        </body>
        </html>"""
        self.wfile.write(error_html.encode('utf-8'))

    def do_GET(self):
        if not self.verify_request_token():
            self.send_forbidden()
            return

        parsed_url = urllib.parse.urlparse(self.path)
        path_only = parsed_url.path

        if path_only == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            try:
                files = os.listdir(SHARED_DIR)
            except Exception:
                files = []

            file_list_html = ""
            for f in sorted(files):
                if f.startswith('.'):
                    continue
                full_path = os.path.join(SHARED_DIR, f)
                if os.path.isdir(full_path):
                    continue

                size_bytes = 0
                try:
                    size_bytes = os.path.getsize(full_path)
                except:
                    pass

                if size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024*1024):.1f} MB"

                encoded_f = urllib.parse.quote(f)
                file_link = f"/{encoded_f}?token={AUTH_TOKEN}"
                
                file_list_html += f"""
                <li class="file-item">
                    <div class="file-info">
                        <div class="file-icon">📄</div>
                        <div>
                            <a href="{file_link}" class="file-link">{f}</a>
                            <span class="file-size">{size_str}</span>
                        </div>
                    </div>
                    <a href="{file_link}" class="download-btn">Download</a>
                </li>
                """

            if not file_list_html:
                file_list_html = '<div style="color:var(--text-secondary); text-align:center; padding: 20px;">No files available in shared_files</div>'

            html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure AirShare LAN</title>
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            --card-bg: rgba(30, 41, 59, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #6366f1;
            --accent-hover: #4f46e5;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        body { background: var(--bg-gradient); color: var(--text-primary); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { width: 100%; max-width: 550px; }
        .header { text-align: center; margin-bottom: 25px; }
        .header h1 { font-size: 1.8rem; background: linear-gradient(to right, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; font-weight: 800; }
        .header p { color: var(--text-secondary); font-size: 0.95rem; }
        .card { background: var(--card-bg); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid var(--border-color); border-radius: 20px; padding: 24px; margin-bottom: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
        .card h2 { font-size: 1.1rem; margin-bottom: 16px; color: var(--text-primary); display: flex; align-items: center; gap: 8px; font-weight: 600; }
        
        .upload-dropzone { border: 2px dashed rgba(99, 102, 241, 0.4); border-radius: 14px; padding: 25px; text-align: center; background: rgba(15, 23, 42, 0.3); transition: all 0.3s ease; cursor: pointer; position: relative; }
        .upload-dropzone:hover { border-color: var(--accent); background: rgba(99, 102, 241, 0.05); }
        .upload-dropzone input { position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
        .upload-text { color: var(--text-secondary); font-size: 0.9rem; margin-top: 8px; }
        .upload-text span { color: var(--accent); font-weight: 600; }
        
        .upload-btn { background: var(--accent); color: white; border: none; padding: 12px; width: 100%; border-radius: 12px; font-weight: 600; font-size: 0.95rem; cursor: pointer; transition: background 0.2s, transform 0.1s; margin-top: 14px; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3); }
        .upload-btn:hover { background: var(--accent-hover); }
        .upload-btn:active { transform: scale(0.98); }

        .file-list { list-style: none; max-height: 320px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-right: 4px; }
        .file-list::-webkit-scrollbar { width: 6px; }
        .file-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
        
        .file-item { display: flex; align-items: center; justify-content: space-between; background: rgba(15, 23, 42, 0.5); padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border-color); transition: border-color 0.2s; }
        .file-item:hover { border-color: rgba(99, 102, 241, 0.4); }
        
        .file-info { display: flex; align-items: center; gap: 12px; overflow: hidden; }
        .file-icon { font-size: 1.4rem; background: rgba(99, 102, 241, 0.1); padding: 8px; border-radius: 10px; }
        .file-link { color: var(--text-primary); text-decoration: none; font-size: 0.95rem; font-weight: 500; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }
        .file-link:hover { color: #818cf8; }
        .file-size { color: var(--text-secondary); font-size: 0.75rem; display: block; margin-top: 2px; }
        
        .download-btn { background: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 6px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; text-decoration: none; transition: all 0.2s; white-space: nowrap; border: 1px solid rgba(99, 102, 241, 0.3); }
        .download-btn:hover { background: var(--accent); color: white; }

        .footer { text-align: center; color: var(--text-secondary); font-size: 0.8rem; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Secure AirShare LAN</h1>
            <p>Lightning-fast local file sharing between devices</p>
        </div>

        <div class="card">
            <h2>📤 Upload File</h2>
            <form method="POST" action="/?token=__AUTH_TOKEN__" enctype="multipart/form-data">
                <div class="upload-dropzone">
                    <div style="font-size: 2rem;">📁</div>
                    <div class="upload-text">Drag & drop file here or <span>browse</span></div>
                    <input type="file" name="file" required onchange="updateFileName(this)">
                </div>
                <div id="file-name" style="font-size: 0.85rem; color: #818cf8; margin-top: 8px; text-align: center; font-weight: 500;"></div>
                <button type="submit" class="upload-btn">Upload to Storage</button>
            </form>
        </div>

        <div class="card">
            <h2>📁 Shared Files</h2>
            <ul class="file-list">
                __FILE_LIST_HTML__
            </ul>
        </div>
        
        <div class="footer">
            100% Secure • Token Protected • Powered by Python
        </div>
    </div>

    <script>
        function updateFileName(input) {
            const fileNameDiv = document.getElementById('file-name');
            if (input.files && input.files[0]) {
                fileNameDiv.textContent = "Selected: " + input.files[0].name;
            }
        }
    </script>
</body>
</html>
"""
            html_content = html_template.replace("__AUTH_TOKEN__", AUTH_TOKEN).replace("__FILE_LIST_HTML__", file_list_html)
            self.wfile.write(html_content.encode('utf-8'))
        else:
            filename = urllib.parse.unquote(path_only.lstrip('/'))
            safe_filename = os.path.basename(filename)
            target_path = os.path.join(SHARED_DIR, safe_filename)
            abs_target = os.path.abspath(target_path)

            if not abs_target.startswith(SHARED_DIR) or not os.path.exists(abs_target) or os.path.isdir(abs_target):
                self.send_forbidden()
                return

            try:
                file_size = os.path.getsize(abs_target)
                with open(abs_target, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{safe_filename}"')
                self.send_header("Content-Length", str(file_size))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_response(500)
                self.end_headers()

    def do_POST(self):
        if not self.verify_request_token():
            self.send_forbidden()
            return

        content_type = self.headers.get('content-type', '')
        content_length = int(self.headers.get('content-length', 0))
        
        if content_length > 0:
            try:
                body = self.rfile.read(content_length)
                header_block = f"Content-Type: {content_type}\r\n\r\n".encode('latin1')
                msg = email.message_from_bytes(header_block + body, policy=email.policy.default)
                
                if msg.is_multipart():
                    for part in msg.iter_parts():
                        filename = part.get_filename()
                        if filename:
                            raw_filename = os.path.basename(filename)
                            safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', raw_filename)
                            if not safe_filename:
                                safe_filename = "uploaded_file"
                            destination_path = os.path.join(SHARED_DIR, safe_filename)
                            payload = part.get_payload(decode=True)
                            if payload:
                                with open(destination_path, 'wb') as output_file:
                                    output_file.write(payload)
                                print(f"[Success] File saved to shared_files: {safe_filename}")
            except Exception as e:
                print(f"Upload Error: {e}")
                self.send_response(500)
                self.end_headers()
                return

        self.send_response(303)
        self.send_header('Location', f'/?token={AUTH_TOKEN}')
        self.end_headers()

if __name__ == '__main__':
    local_ip = get_local_ip()
    localhost_url = f"http://127.0.0.1:{PORT}/?token={AUTH_TOKEN}"
    network_url = f"http://{local_ip}:{PORT}/?token={AUTH_TOKEN}"
    
    print("\n" + "=" * 50)
    print(" 🚀 SECURE AIRSHARE LAN SERVER STARTED")
    print("=" * 50)
    print(f" Localhost Link : {localhost_url}")
    print(f" Network Wi-Fi  : {network_url}")
    print("=" * 50)
    
    print_qr_code(network_url)
    
    print(f" Shared Files Folder: {SHARED_DIR}")
    print(" Opening browser automatically...")
    print(" Press Ctrl + C to stop the server.\n")

    threading.Timer(1.0, lambda: webbrowser.open(localhost_url)).start()

    server_address = ('', PORT)
    with socketserver.TCPServer(server_address, SecureAirShareHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped. Goodbye!")