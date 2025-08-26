import os

bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = int(os.environ.get('WEB_CONCURRENCY', 4))
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 2
preload_app = True

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get('LOG_LEVEL', 'info').lower()

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")