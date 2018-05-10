"""
This script runs the visualizer application using a development server.
"""

from os import environ
from visualizer import app


if __name__ == '__main__':

    HOST = environ.get('SERVER_HOST', '0.0.0.0')
    try:
        PORT = int(environ.get('SERVER_PORT', '80'))
    except ValueError:
        PORT = 5555

    app.run(HOST, PORT)
