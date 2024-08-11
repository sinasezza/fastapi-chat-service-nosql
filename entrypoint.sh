#!/bin/bash
set -e

RUN_PORT=${RUN_PORT:-8000}

exec uvicorn chatApp.main:app --host 0.0.0.0 --port ${RUN_PORT}
