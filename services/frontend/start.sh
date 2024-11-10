#!/bin/bash
cd /app/src
http-server -p 8080 &
P1=$!

wait $P1