from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        # 允许跨域，防止小手机客户端请求被拦
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    # 处理跨域预检请求
    def do_OPTIONS(self):
        self._set_headers(200)

    # 处理 GET 测试请求
    def do_GET(self):
        self._set_headers(200)
        response = {
            "status": "ok",
            "message": "小手机 Remote MCP 服务正常运行中"
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    # 处理小手机发过来的 MCP / API POST 请求
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        # 响应正常的 MCP 心跳/测试返回
        self._set_headers(200)
        response = {
            "jsonrpc": "2.0",
            "result": {
                "status": "success",
                "message": "已成功接收 MCP 请求"
            },
            "id": None
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
