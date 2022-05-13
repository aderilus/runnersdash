""" Dash dashboard entry point.

USAGE:
    $ python app.py
"""

import webbrowser
from threading import Timer
from dashboard.content import app


def open_dash_link():
    """ Open browser automatically once `run_server` is called.
    """
    webbrowser.open_new('http://127.0.0.1:8050/')


def generate_dash_server(toggle_debug=False):
    Timer(1, open_dash_link).start()
    app.run_server(debug=toggle_debug)


if __name__ == '__main__':
    generate_dash_server(True)
