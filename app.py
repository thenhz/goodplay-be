#!/usr/bin/env python3

import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    debug = os.environ.get('FLASK_ENV') == 'development'

    # Use socketio.run() instead of app.run() for WebSocket support
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=True,
        log_output=debug
    )