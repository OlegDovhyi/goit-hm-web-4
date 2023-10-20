from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import urllib.parse
import mimetypes
import pathlib
import threading
import json
import socket

json_data = {}

class MainServer(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data_parse = urllib.parse.parse_qs(post_data)

        username = data_parse.get('username', [''])[0]
        message = data_parse.get('message', [''])[0]

        if username and message:
            current_time = str(datetime.now())
            json_data[current_time] = {'username': username, 'message': message}
            with open(pathlib.Path().joinpath('storage/data.json'), 'w', encoding='utf-8') as fd:
                json.dump(json_data, fd, ensure_ascii=False)

            # Sending data to socket server
            self.send_to_socket_server(current_time, username, message)

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_to_socket_server(self, timestamp, username, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = ('localhost', 5000)
        data = {'timestamp': timestamp, 'username': username, 'message': message}
        message = json.dumps(data).encode('utf-8')
        sock.sendto(message, server_address)
        sock.close()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        try:
            self.send_response(200)
            mt = mimetypes.guess_type(self.path)
            if mt:
                self.send_header("Content-type", mt[0])
            else:
                self.send_header("Content-type", 'text/plain')
            self.end_headers()
            with open(f'.{self.path}', 'rb') as file:
                self.wfile.write(file.read())
        except ConnectionAbortedError:
            print("Соединение было разорвано клиентом.")


def run(server_class=HTTPServer, handler_class=MainServer):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http_server = threading.Thread(target=http.serve_forever)
        http_server.start()
    except KeyboardInterrupt:
        http.server_close()

if __name__ == '__main__':
    run()
