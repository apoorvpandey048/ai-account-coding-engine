#!/bin/bash
# Azure App Service startup script

# Start the application with uvicorn (simpler for Linux App Service)
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 2
