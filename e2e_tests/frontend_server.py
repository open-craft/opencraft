# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2020 OpenCraft <xavier@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Utility functions related to frontend server for e2e testing.
"""
import http.server
import os

from urllib.parse import urlparse
from threading import Thread


# Functions #################################################################

def start_react_server(
        build_path="./frontend/build",
        hostname="localhost",
        port=3000
):
    """
    Start a react server in different thread.
    """
    build_path = os.path.abspath(build_path)
    handler = RequestHandler
    httpd = http.server.HTTPServer((hostname, port), handler, False)

    httpd.server_bind()
    address = "http://%s:%d" % (httpd.server_name, httpd.server_port)

    print("Server starting at:", address)
    httpd.server_activate()

    def serve_forever(httpd):
        # Switch to the frontend build directory
        os.chdir(build_path)
        with httpd:  # to make sure httpd.server_close is called
            print("Frontend server started (infinite request loop):", build_path)
            httpd.serve_forever()
            print("Shutting down frontend server")

    thread = Thread(target=serve_forever, args=(httpd, ))
    thread.setDaemon(True)
    thread.start()

    return httpd, address


# Classes ################################################################

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    RequestHandler for react frontend server. We send the index file
    instead of 404.
    """

    INDEXFILE = "index.html"

    def log_message(self, format, *args): # pylint: disable=redefined-builtin
        """
        Override to supress logs of accessed paths.
        """

    def do_GET(self): # noqa
        """
        Override get method to send the INDEXFILE when the requested file is not found.
        """
        parsed_params = urlparse(self.path)

        try:
            # See if the file requested exists and accessible
            if os.access('.' + os.sep + parsed_params.path, os.R_OK):
                http.server.SimpleHTTPRequestHandler.do_GET(self)
            else:
                # send index.html, but don't redirect
                index_file = os.path.join(os.getcwd(), self.INDEXFILE)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                with open(index_file, 'rb') as fin:
                    self.copyfile(fin, self.wfile)
        except BrokenPipeError:
            # The client closed connection. We can ignore the exception here.
            pass
