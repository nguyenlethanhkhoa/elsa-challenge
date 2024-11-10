#!/bin/bash

python setup.py

uvicorn main:app --host 0.0.0.0 --port 8000