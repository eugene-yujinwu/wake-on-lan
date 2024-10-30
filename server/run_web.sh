#!/bin/bash

echo "Start Wake-On-Lan server"
uvicorn wol_server:app --host 0.0.0.0 --port 8090
