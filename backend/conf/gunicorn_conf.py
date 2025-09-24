# gunicorn_conf.py
import os

os.makedirs("logs/gunicorn", exist_ok=True)

bind = "0.0.0.0:8000"
workers = int(os.environ.get("GUNICORN_WORKERS", "1"))
worker_class = "uvicorn.workers.UvicornWorker"
reload = True
forwarded_allow_ips = "*"
capture_output = True
enable_stdio_inheritance = True
loglevel = "debug"
timeout = 600
