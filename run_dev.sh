#!/usr/bin/env bash
set -e
export PYTHONUNBUFFERED=1
echo "Starting dev server at http://127.0.0.1:8000 ..."
uvicorn app.main:app --reload
