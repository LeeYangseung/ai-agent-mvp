#!/bin/sh
cd "$(dirname "$0")" && UVICORN_LOG_LEVEL=debug gunicorn app.main:app -c ./conf/gunicorn_conf.py --reload