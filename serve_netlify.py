import http.server
import socketserver

PORT = 8080
DIRECTORY = "build_web_netlify"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

if __name__ == "__main__":
    handler = MyHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print(f"Serving build_web_netlify on port {PORT} with COOP/COEP headers...")
            print(f"Local test URL: http://localhost:{PORT}/")
            print("Press Ctrl+C to stop the server.")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
