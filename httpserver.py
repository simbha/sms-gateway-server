"""
Module containing classes to implement a HTTP server that accepts message
requests & places them in a queue to be processed.
"""

# Standard library modules
import BaseHTTPServer
import cgi
import md5
import os
import socket
import sys
import time

# Local application modules
from sms_gateway_server import __version__, APP_NAME
import util

class StoppableHTTPServer(BaseHTTPServer.HTTPServer):
    """
    Subclass of BaseHTTPServer.HTTPServer to provide a stoppable HTTP server.
    This is done by setting a timeout when accepting socket connections. This
    allows the server to be arbitrarily started & stopped. (Without a timeout
    the "handle_request" method will block until a request is received)
    """
    def __init__(self, log_http_data, message_received, *args):
        """
        The "log_http_data" parameter is a function/method that is called when
        the server logs a request. Refer to HTTPHandler.log_message to see the
        function being used.

        The "message_received" parameter is a function/method that is called
        when a new message request is received. Refer to HTTPHandler.do_POST to
        see the function being used.
        """
        self.log_http_data = log_http_data
        self.message_received = message_received

        BaseHTTPServer.HTTPServer.__init__(self, *args)

    def server_bind(self):
        """
        Overrides the "server_bind" method to provide a timeout on the socket
        connection.
        """
        self.is_running = True
        self.socket.settimeout(1)
        BaseHTTPServer.HTTPServer.server_bind(self)

    def get_request(self):
        """
        Overrides the "server_bind" method to provide handling of socket
        timeouts.
        """
        while self.is_running:
            try:
                sock, addr = self.socket.accept()
                sock.settimeout(None)
                return (sock, addr)
            except socket.timeout:
                if not self.is_running:
                    raise socket.error

    def stop(self):
        """
        Signals to the server to stop accepting requests.
        """
        self.is_running = False

    def serve(self):
        """
        Signals to the server to start accepting requests.
        """
        while self.is_running:
            self.handle_request()


class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def version_string(self):
        """
        Returns the server software version string.
        """
        return '%s/%s' % (APP_NAME.replace(' ', ''), __version__)

    def do_GET(self):
        """
        Handles GET requests to the server.
        """
        if self.path == '/sms_sender.html':

            # Get the server hostname & port
            hostname = self.server.server_name
            port = self.server.server_address[1]

            # Open the SMS sender HTML form & replace the server/port information
            file_path = os.path.join(os.path.dirname(sys.argv[0]), 'public_html/sms_sender.html')
            response_data = open(file_path, 'r').read()
            response_data = response_data.replace('${SERVER}', hostname if port == 80 else '%s:%d' % (hostname, port))
            response_data = response_data.replace('${VERSION}', self.version_string())
            response_data = response_data.replace('\t', '')

            # Calculate the server ETag header & get the client ETag header
            hash = md5.new()
            hash.update(response_data)
            server_etag = hash.hexdigest()
            client_etag = self.headers.getheader('If-None-Match')

            # Get the last modified date of the file & the client modified date
            server_modified = util.get_modified_datetime(file_path)
            client_modified = self.headers.getheader('If-Modified-Since')

            # Send a "304 Not modified" response if the content has not changed
            if client_etag == server_etag or server_modified == client_modified:
                self.send_response(304)
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', len(response_data))
                self.send_header('ETag', server_etag)
                self.send_header('Cache-Control', 'max-age=%d' % util.secs_from_days(7))
                self.send_header('Last-Modified', server_modified)
                self.send_header('Expires', util.get_http_expiry(7))
                self.end_headers()
                self.wfile.write(response_data)

        elif self.path == '/sms_sender.css':
            file_path = os.path.join(os.path.dirname(sys.argv[0]), 'public_html/sms_sender.css')

            # Calculate the server ETag header & get the client ETag header
            hash = md5.new()
            hash.update(str(os.path.getmtime(file_path)))
            server_etag = hash.hexdigest()
            client_etag = self.headers.getheader('If-None-Match')

            # Get the last modified date of the file & the client modified date
            server_modified = util.get_modified_datetime(file_path)
            client_modified = self.headers.getheader('If-Modified-Since')

            # Send a "304 Not modified" response if the content has not changed
            if client_etag == server_etag or server_modified == client_modified:
                self.send_response(304)
                self.end_headers()
            else:
                response_data = open(file_path, 'r').read()
                response_data = response_data.replace('\t', '')
                self.send_response(200)
                self.send_header('Content-Type', 'text/css')
                self.send_header('Content-Length', len(response_data))
                self.send_header('ETag', server_etag)
                self.send_header('Cache-Control', 'max-age=%d' % util.secs_from_days(7))
                self.send_header('Expires', util.get_http_expiry(7))
                self.send_header('Last-Modified', server_modified)
                self.end_headers()
                self.wfile.write(response_data)

        elif self.path == '/' or self.path.endswith('.html') or self.path.endswith('.htm'):
                self.send_response(302)
                self.send_header('Location', '/sms_sender.html')
                self.end_headers()

        else:
            self.serve_message(404, 'Page Not Found', 'The requested page could not be found.')

    def do_POST(self):
        """
        Handles POST requests to the server.
        """

        # Get a timestamp for the request
        timestamp = time.strftime('%d/%m/%y %H:%M:%S')

        # Redirect any POST request that does not match the current URL
        if not self.path == '/send_message':
            self.send_response(303)
            self.send_header('Location', '/sms_sender.html')
            self.end_headers()
            return

        # Get the length of the POST content
        content_length = int(self.headers.getheader('content-length'))

        # If there is POST content then process it
        if content_length:

            # Get the form data
            post_data = cgi.parse_qs(self.rfile.read(content_length))
            try:
                recipients = post_data['recipients'][0]
                message = post_data['message'][0]
            except KeyError, IndexError:
                self.serve_message(400, 'Error', 'The message request was missing either recipient or message data.')
                return

            # Check if message class is defined, if not default to '1'
            # Class 0 = Message is displayed but not stored on phone
            # Class 1 = Store the message on the phone
            # Class 2 = Store the message on the SIM card
            try:
                msg_class = post_data['class'][0]
            except KeyError, IndexError:
                msg_class = '1'

            # Validate the recipient data
            for char in recipients:
                if char not in ';+0123456789 \t':
                    self.serve_message(400, 'Error', 'The recipient data contains an invalid character ("%s").' % char)
                    return

            # Validate the SMS class data
            try:
                msg_class = int(msg_class)
            except ValueError:
                self.serve_message(400, 'Error', 'The given SMS class is invalid.')

            if not 0 <= msg_class <= 2:
                self.serve_message(400, 'Error', 'The SMS class can only be either 0, 1 or 2.')
                return

            # Get a list of recipients from the recipient string
            recipient_list = [x.strip() for x in recipients.split(';') if x]

            for recipient in recipient_list:
                self.server.message_received({'timestamp': timestamp,
                                              'recipient': recipient,
                                              'class': msg_class,
                                              'message': message,
                                              'sender_ip': self.client_address[0]})

            self.serve_message(200, 'Message(s) Queued', 'Your message(s) have been added to the queue to be sent.')

    def log_message(self, *args):
        self.server.log_http_data('%s - %s:%d - %s - %s' % (time.strftime('%d/%m/%y %H:%M:%S'),
                                                            self.client_address[0],
                                                            self.client_address[1],
                                                            self.requestline,
                                                            self.headers.getheader('User-Agent')))

    def serve_message(self, status_code, title, message):
        file_path = os.path.join(os.path.dirname(sys.argv[0]), 'public_html/page.html')
        response_data = open(file_path, 'r').read()
        response_data = response_data.replace('${TITLE}', cgi.escape(title))
        response_data = response_data.replace('${MESSAGE}', cgi.escape(message))
        response_data = response_data.replace('${VERSION}', self.version_string())
        response_data = response_data.replace('\t', '')

        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(response_data))
        self.end_headers()
        self.wfile.write(response_data)
