from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import os
import webbrowser  # 添加webbrowser模块

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == "__main__":
    # 切换到项目根目录
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    httpd = HTTPServer(('localhost', 8000), CORSRequestHandler)
    print("静态文件服务器运行在 http://localhost:8000")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 自动打开浏览器
    webbrowser.open('http://localhost:8000/frontend/html/index.html')
    
    httpd.serve_forever() 