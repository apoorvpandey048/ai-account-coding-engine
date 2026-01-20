#!/bin/bash
# Azure App Service startup script

# Install dependencies if needed
pip install -r requirements.txt

# Start the application with gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.main_poc:app --bind 0.0.0.0:8000 --timeout 600
