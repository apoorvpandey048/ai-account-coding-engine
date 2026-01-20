#!/bin/bash
# Azure App Service startup script for Oryx

# Oryx sets PYTHONPATH automatically, just use gunicorn with the module path
exec gunicorn --bind 0.0.0.0:8000 \
     --worker-class uvicorn.workers.UvicornWorker \
     --workers 2 \
     --timeout 600 \
     --access-logfile '-' \
     --error-logfile '-' \
     --log-level info \
     src.api.main:app
